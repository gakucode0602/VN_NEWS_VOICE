package com.pmq.vnnewsvoice.article.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
public class ApiResponse<T> {
  private boolean success;
  private int code;
  private String message;
  private T result;

  public static <T> ApiResponse<T> ok(T result) {
    return ApiResponse.<T>builder()
        .success(true)
        .code(200)
        .message("Success")
        .result(result)
        .build();
  }

  public static <T> ApiResponse<T> ok(String message, T result) {
    return ApiResponse.<T>builder().success(true).code(200).message(message).result(result).build();
  }

  public static <T> ApiResponse<T> error(int code, String message) {
    return ApiResponse.<T>builder().success(false).code(code).message(message).build();
  }
}
