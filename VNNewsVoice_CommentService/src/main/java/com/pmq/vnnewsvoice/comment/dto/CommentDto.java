package com.pmq.vnnewsvoice.comment.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import java.util.Date;
import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/** Response DTO for a single comment. */
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public class CommentDto {
  private Long id;
  private String content;
  private Date createdAt;

  // Article reference (cross-service — id only, no title/slug fetched)
  private String articleId;

  // User who wrote the comment (denormalized at write time)
  private Long userId;
  private String username;

  // Self-reference for threaded replies (null = top-level comment)
  private Long commentReplyId;

  // Aggregated metrics
  private Long likeCount;

  // Nested replies (populated only on detail endpoint, not list)
  private List<CommentDto> replies;
}
