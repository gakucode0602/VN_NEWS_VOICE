package com.pmq.vnnewsvoice.comment.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class CommentLikeDto {
  private Long commentId;
  private boolean isLiked;
  private Long likeCount;
}
