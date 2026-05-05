package com.pmq.vnnewsvoice.comment.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * Request DTO for creating a comment. Content is provided by the user; userId/username from JWT.
 */
@Getter
@Setter
@NoArgsConstructor
public class CommentRequest {

  @NotBlank(message = "Nội dung bình luận không được để trống")
  @Size(min = 1, max = 2000, message = "Nội dung phải từ 1 đến 2000 ký tự")
  private String content;

  // Optional: id of the parent comment being replied to (null = top-level comment)
  private Long commentReplyId;
}
