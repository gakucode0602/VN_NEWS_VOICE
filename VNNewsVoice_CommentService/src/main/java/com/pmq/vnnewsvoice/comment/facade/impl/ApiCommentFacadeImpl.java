package com.pmq.vnnewsvoice.comment.facade.impl;

import com.pmq.vnnewsvoice.comment.dto.ApiResult;
import com.pmq.vnnewsvoice.comment.dto.CommentDto;
import com.pmq.vnnewsvoice.comment.dto.CommentListResponse;
import com.pmq.vnnewsvoice.comment.dto.CommentRequest;
import com.pmq.vnnewsvoice.comment.dto.Pagination;
import com.pmq.vnnewsvoice.comment.facade.ApiCommentFacade;
import com.pmq.vnnewsvoice.comment.helpers.PaginationHelper;
import com.pmq.vnnewsvoice.comment.mapper.CommentMapper;
import com.pmq.vnnewsvoice.comment.pojo.Comment;
import com.pmq.vnnewsvoice.comment.pojo.CustomUserDetails;
import com.pmq.vnnewsvoice.comment.service.CommentLikeService;
import com.pmq.vnnewsvoice.comment.service.CommentService;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Service
@RequiredArgsConstructor
@Slf4j
public class ApiCommentFacadeImpl implements ApiCommentFacade {

  private final CommentService commentService;
  private final CommentLikeService commentLikeService;
  private final CommentMapper commentMapper;
  private final PaginationHelper paginationHelper;

  @Override
  public ApiResult<CommentListResponse> getCommentsByArticleId(
      String articleId, Map<String, String> params) {
    if (!StringUtils.hasText(articleId)) {
      return ApiResult.failure(HttpStatus.BAD_REQUEST, "Article ID không hợp lệ");
    }

    List<Comment> comments = commentService.getTopLevelCommentsByArticleId(articleId, params);
    long total = commentService.countCommentsByArticleId(articleId);
    long topLevelTotal = commentService.countTopLevelCommentsByArticleId(articleId);
    Pagination pagination = paginationHelper.createPagination(params, topLevelTotal, 10);
    // Override totalItems with the full comment count so the UI displays meaningful number
    pagination.setTotalItems(total);

    // Map to DTOs and enrich with likeCount + nested replies
    List<CommentDto> dtos =
        comments.stream()
            .map(
                comment -> {
                  CommentDto dto = commentMapper.toDto(comment);
                  dto.setLikeCount(commentLikeService.countLikesByCommentId(comment.getId()));
                  // Populate replies for each top-level comment
                  List<CommentDto> replyDtos =
                      commentService.getRepliesByParentId(comment.getId()).stream()
                          .map(
                              reply -> {
                                CommentDto replyDto = commentMapper.toDto(reply);
                                replyDto.setLikeCount(
                                    commentLikeService.countLikesByCommentId(reply.getId()));
                                return replyDto;
                              })
                          .toList();
                  dto.setReplies(replyDtos);
                  return dto;
                })
            .toList();

    return ApiResult.success(HttpStatus.OK, new CommentListResponse(dtos, pagination));
  }

  @Override
  public ApiResult<CommentDto> getCommentById(Long id) {
    if (id == null || id <= 0) {
      return ApiResult.failure(HttpStatus.BAD_REQUEST, "Comment ID không hợp lệ");
    }

    Optional<Comment> optComment = commentService.getCommentById(id);
    if (optComment.isEmpty() || optComment.get().isDeleted()) {
      return ApiResult.failure(HttpStatus.NOT_FOUND, "Không tìm thấy bình luận");
    }

    Comment comment = optComment.get();
    CommentDto dto = commentMapper.toDto(comment);
    dto.setLikeCount(commentLikeService.countLikesByCommentId(id));

    // Populate nested replies
    List<CommentDto> replyDtos =
        commentService.getRepliesByParentId(id).stream()
            .map(
                reply -> {
                  CommentDto replyDto = commentMapper.toDto(reply);
                  replyDto.setLikeCount(commentLikeService.countLikesByCommentId(reply.getId()));
                  return replyDto;
                })
            .toList();
    dto.setReplies(replyDtos);

    return ApiResult.success(HttpStatus.OK, dto);
  }

  @Override
  public ApiResult<CommentListResponse> getCommentsByCurrentUser(
      Map<String, String> params, CustomUserDetails principal) {
    Long userId = principal.getUserId();

    List<Comment> comments = commentService.getCommentsByUserId(userId, params);
    long total = commentService.countCommentsByUserId(userId);
    Pagination pagination = paginationHelper.createPagination(params, total, 10);

    List<CommentDto> dtos =
        comments.stream()
            .map(
                comment -> {
                  CommentDto dto = commentMapper.toDto(comment);
                  dto.setLikeCount(commentLikeService.countLikesByCommentId(comment.getId()));
                  return dto;
                })
            .toList();

    return ApiResult.success(HttpStatus.OK, new CommentListResponse(dtos, pagination));
  }

  @Override
  public ApiResult<CommentDto> createComment(
      CommentRequest request, String articleId, CustomUserDetails principal) {
    if (!StringUtils.hasText(articleId)) {
      return ApiResult.failure(HttpStatus.BAD_REQUEST, "Article ID không hợp lệ");
    }

    Comment comment = new Comment();
    comment.setContent(request.getContent());
    comment.setArticleId(articleId);
    comment.setUserId(principal.getUserId());
    comment.setUsername(principal.getUsername()); // denormalize at write time

    // Handle reply
    if (request.getCommentReplyId() != null) {
      Optional<Comment> parentOpt = commentService.getCommentById(request.getCommentReplyId());
      if (parentOpt.isEmpty() || parentOpt.get().isDeleted()) {
        return ApiResult.failure(HttpStatus.BAD_REQUEST, "Bình luận gốc không tồn tại");
      }
      comment.setCommentReply(parentOpt.get());
    }

    Comment saved = commentService.addComment(comment);
    log.info(
        "Comment created: id={} by user={} on article={}",
        saved.getId(),
        principal.getUserId(),
        articleId);

    CommentDto dto = commentMapper.toDto(saved);
    dto.setLikeCount(0L);
    return ApiResult.success(HttpStatus.CREATED, dto);
  }

  @Override
  public ApiResult<Void> deleteComment(Long commentId, CustomUserDetails principal) {
    if (commentId == null || commentId <= 0) {
      return ApiResult.failure(HttpStatus.BAD_REQUEST, "Comment ID không hợp lệ");
    }

    Optional<Comment> optComment = commentService.getCommentById(commentId);
    if (optComment.isEmpty() || optComment.get().isDeleted()) {
      return ApiResult.failure(HttpStatus.NOT_FOUND, "Không tìm thấy bình luận");
    }

    // Only the owner can delete their own comment
    Comment comment = optComment.get();
    if (!comment.getUserId().equals(principal.getUserId())) {
      return ApiResult.failure(HttpStatus.FORBIDDEN, "Bạn không có quyền xóa bình luận này");
    }

    commentService.softDeleteComment(commentId);
    log.info("Comment soft-deleted: id={} by user={}", commentId, principal.getUserId());
    return ApiResult.success(HttpStatus.OK, null);
  }
}
