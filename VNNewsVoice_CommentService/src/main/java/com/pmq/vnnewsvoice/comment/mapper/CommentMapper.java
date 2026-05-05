package com.pmq.vnnewsvoice.comment.mapper;

import com.pmq.vnnewsvoice.comment.dto.CommentDto;
import com.pmq.vnnewsvoice.comment.pojo.Comment;
import java.util.List;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper(componentModel = "spring")
public interface CommentMapper {

  @Mapping(
      target = "commentReplyId",
      expression =
          "java(comment.getCommentReply() != null ? comment.getCommentReply().getId() : null)")
  @Mapping(target = "likeCount", ignore = true) // populated by facade from CommentLikeService
  @Mapping(target = "replies", ignore = true) // populated by facade on detail endpoint only
  CommentDto toDto(Comment comment);

  List<CommentDto> toDtoList(List<Comment> comments);
}
