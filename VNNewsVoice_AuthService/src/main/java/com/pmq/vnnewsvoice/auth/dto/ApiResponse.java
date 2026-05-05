package com.pmq.vnnewsvoice.auth.dto;

import lombok.*;

@Builder
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class ApiResponse<T> {
  @Builder.Default private boolean success = true;
  @Builder.Default private int code = 200;
  private String message;
  private T result;
}
