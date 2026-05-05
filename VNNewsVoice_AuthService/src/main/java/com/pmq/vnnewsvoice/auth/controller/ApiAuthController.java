package com.pmq.vnnewsvoice.auth.controller;

import com.pmq.vnnewsvoice.auth.dto.ApiResponse;
import com.pmq.vnnewsvoice.auth.dto.ApiResult;
import com.pmq.vnnewsvoice.auth.dto.AuthRequest;
import com.pmq.vnnewsvoice.auth.dto.AuthResponse;
import com.pmq.vnnewsvoice.auth.dto.GoogleLoginDto;
import com.pmq.vnnewsvoice.auth.dto.GoogleLoginResponse;
import com.pmq.vnnewsvoice.auth.dto.ReaderDto;
import com.pmq.vnnewsvoice.auth.dto.RegisterReaderDto;
import com.pmq.vnnewsvoice.auth.facade.ApiAuthFacade;
import com.pmq.vnnewsvoice.auth.helpers.CookieHelper;
import com.pmq.vnnewsvoice.auth.service.LoginRateLimiterService;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import java.io.IOException;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseCookie;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.*;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api")
public class ApiAuthController {
  private final ApiAuthFacade apiAuthFacade;
  private final CookieHelper cookieHelper;
  private final LoginRateLimiterService loginRateLimiterService;

  @PostMapping("/user/register")
  public ResponseEntity<ApiResponse<ReaderDto>> create(
      @Valid @ModelAttribute RegisterReaderDto registerReaderDto, BindingResult bindingResult)
      throws IOException {
    if (bindingResult.hasErrors()) {
      return ResponseEntity.status(HttpStatus.BAD_REQUEST)
          .body(
              ApiResponse.<ReaderDto>builder()
                  .success(false)
                  .code(HttpStatus.BAD_REQUEST.value())
                  .message("Dữ liệu không hợp lệ")
                  .build());
    }
    ApiResult<ReaderDto> result = apiAuthFacade.registerReader(registerReaderDto);
    return buildResponse(result);
  }

  @PostMapping("/user/login")
  public ResponseEntity<ApiResponse<AuthResponse>> login(
      @RequestBody @Valid AuthRequest authRequest) {
    if (!loginRateLimiterService.tryConsume(authRequest.getUsername())) {
      return ResponseEntity.status(HttpStatus.TOO_MANY_REQUESTS)
          .body(
              ApiResponse.<AuthResponse>builder()
                  .success(false)
                  .code(HttpStatus.TOO_MANY_REQUESTS.value())
                  .message("Quá nhiều lần đăng nhập. Vui lòng thử lại sau 1 phút.")
                  .build());
    }
    ApiResult<AuthResponse> result = apiAuthFacade.login(authRequest);
    return buildAuthResponseWithCookie(result);
  }

  @PostMapping("/user/google-login")
  public ResponseEntity<ApiResponse<GoogleLoginResponse>> googleLogin(
      @RequestBody GoogleLoginDto googleLoginDto) {
    try {
      ApiResult<GoogleLoginResponse> result = apiAuthFacade.googleLogin(googleLoginDto);
      return buildGoogleLoginResponseWithCookie(result);
    } catch (Exception e) {
      return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
          .header(HttpHeaders.SET_COOKIE, cookieHelper.clearRefreshTokenCookie().toString())
          .body(
              ApiResponse.<GoogleLoginResponse>builder()
                  .success(false)
                  .code(HttpStatus.UNAUTHORIZED.value())
                  .message(e.getMessage())
                  .build());
    }
  }

  @PostMapping("/auth/refresh")
  public ResponseEntity<ApiResponse<AuthResponse>> refresh(HttpServletRequest request) {
    String refreshToken = extractRefreshToken(request);
    if (refreshToken == null || refreshToken.isBlank()) {
      // Do NOT send Set-Cookie here. Sending clearRefreshTokenCookie() when the cookie is simply
      // absent (e.g. cross-origin SameSite restriction) would delete a still-valid refresh token
      // that the browser holds for same-origin paths.
      return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
          .body(
              ApiResponse.<AuthResponse>builder()
                  .success(false)
                  .code(HttpStatus.UNAUTHORIZED.value())
                  .message("Thiếu refresh token")
                  .build());
    }

    ApiResult<AuthResponse> result = apiAuthFacade.refresh(refreshToken);
    return buildAuthResponseWithCookie(result);
  }

  @PostMapping("/auth/logout")
  public ResponseEntity<ApiResponse<Void>> logout(HttpServletRequest request) {
    String refreshToken = extractRefreshToken(request);
    ApiResult<Void> result =
        (refreshToken == null || refreshToken.isBlank())
            ? ApiResult.success(HttpStatus.OK, null, "Đăng xuất thành công")
            : apiAuthFacade.logout(refreshToken);

    return ResponseEntity.status(result.getStatus())
        .header(HttpHeaders.SET_COOKIE, cookieHelper.clearRefreshTokenCookie().toString())
        .body(
            ApiResponse.<Void>builder()
                .success(result.isSuccess())
                .code(result.getStatus().value())
                .message(result.getMessage())
                .result(result.getResult())
                .build());
  }

  private ResponseEntity<ApiResponse<AuthResponse>> buildAuthResponseWithCookie(
      ApiResult<AuthResponse> result) {
    String refreshToken = result.getResult() != null ? result.getResult().getRefreshToken() : null;
    ResponseCookie cookie =
        (result.isSuccess() && refreshToken != null && !refreshToken.isBlank())
            ? cookieHelper.createRefreshTokenCookie(refreshToken)
            : cookieHelper.clearRefreshTokenCookie();

    return ResponseEntity.status(result.getStatus())
        .header(HttpHeaders.SET_COOKIE, cookie.toString())
        .body(
            ApiResponse.<AuthResponse>builder()
                .success(result.isSuccess())
                .code(result.getStatus().value())
                .message(result.getMessage())
                .result(result.getResult())
                .build());
  }

  private ResponseEntity<ApiResponse<GoogleLoginResponse>> buildGoogleLoginResponseWithCookie(
      ApiResult<GoogleLoginResponse> result) {
    String refreshToken = result.getResult() != null ? result.getResult().getRefreshToken() : null;
    ResponseCookie cookie =
        (result.isSuccess() && refreshToken != null && !refreshToken.isBlank())
            ? cookieHelper.createRefreshTokenCookie(refreshToken)
            : cookieHelper.clearRefreshTokenCookie();

    return ResponseEntity.status(result.getStatus())
        .header(HttpHeaders.SET_COOKIE, cookie.toString())
        .body(
            ApiResponse.<GoogleLoginResponse>builder()
                .success(result.isSuccess())
                .code(result.getStatus().value())
                .message(result.getMessage())
                .result(result.getResult())
                .build());
  }

  private String extractRefreshToken(HttpServletRequest request) {
    Cookie[] cookies = request.getCookies();
    if (cookies == null || cookies.length == 0) {
      return null;
    }

    String cookieName = cookieHelper.getRefreshCookieName();
    for (Cookie cookie : cookies) {
      if (cookieName.equals(cookie.getName())) {
        return cookie.getValue();
      }
    }

    return null;
  }

  private <T> ResponseEntity<ApiResponse<T>> buildResponse(ApiResult<T> result) {
    return ResponseEntity.status(result.getStatus())
        .body(
            ApiResponse.<T>builder()
                .success(result.isSuccess())
                .code(result.getStatus().value())
                .message(result.getMessage())
                .result(result.getResult())
                .build());
  }
}
