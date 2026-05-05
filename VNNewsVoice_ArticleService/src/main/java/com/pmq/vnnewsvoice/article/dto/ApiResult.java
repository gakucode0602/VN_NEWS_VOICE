package com.pmq.vnnewsvoice.article.dto;

import lombok.Getter;
import org.springframework.http.HttpStatus;

@Getter
public class ApiResult<T> {
  private final HttpStatus status;
  private final String message;
  private final T result;

  private ApiResult(HttpStatus status, String message, T result) {
    this.status = status;
    this.message = message;
    this.result = result;
  }

  public static <T> ApiResult<T> success(HttpStatus status, T result) {
    return new ApiResult<>(status, null, result);
  }

  public static <T> ApiResult<T> success(HttpStatus status, T result, String message) {
    return new ApiResult<>(status, message, result);
  }

  public static <T> ApiResult<T> failure(HttpStatus status, String message) {
    return new ApiResult<>(status, message, null);
  }

  public boolean isSuccess() {
    return status.is2xxSuccessful();
  }
}
