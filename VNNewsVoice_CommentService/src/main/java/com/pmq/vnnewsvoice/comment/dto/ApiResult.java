package com.pmq.vnnewsvoice.comment.dto;

import lombok.Getter;
import org.springframework.http.HttpStatus;

@Getter
public class ApiResult<T> {
  private final HttpStatus status;
  private final boolean success;
  private final String message;
  private final T result;

  private ApiResult(HttpStatus status, boolean success, String message, T result) {
    this.status = status;
    this.success = success;
    this.message = message;
    this.result = result;
  }

  public static <T> ApiResult<T> success(HttpStatus status, T result) {
    return new ApiResult<>(status, true, null, result);
  }

  public static <T> ApiResult<T> failure(HttpStatus status, String message) {
    return new ApiResult<>(status, false, message, null);
  }
}
