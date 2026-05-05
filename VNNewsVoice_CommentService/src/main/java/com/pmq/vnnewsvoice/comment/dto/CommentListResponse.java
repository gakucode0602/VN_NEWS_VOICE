package com.pmq.vnnewsvoice.comment.dto;

import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class CommentListResponse {
  private List<CommentDto> comments;
  private Pagination pagination;
}
