package com.pmq.vnnewsvoice.auth.controller;

import com.pmq.vnnewsvoice.auth.dto.ApiResponse;
import com.pmq.vnnewsvoice.auth.dto.ApiResult;
import com.pmq.vnnewsvoice.auth.dto.ReaderDto;
import com.pmq.vnnewsvoice.auth.facade.ApiReaderFacade;
import com.pmq.vnnewsvoice.auth.pojo.CustomUserDetails;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api")
public class ApiReaderController {
  private final ApiReaderFacade apiReaderFacade;

  @GetMapping("/secure/profile")
  @PreAuthorize("hasRole('READER')")
  public ResponseEntity<ApiResponse<ReaderDto>> getProfile(
      @AuthenticationPrincipal CustomUserDetails principal) {
    ApiResult<ReaderDto> result = apiReaderFacade.getProfile(principal);
    return buildResponse(result);
  }

  @PostMapping("/secure/profile")
  @PreAuthorize("hasRole('READER')")
  public ResponseEntity<ApiResponse<Void>> updateProfile(
      @RequestParam("userIdUsername") String username,
      @RequestParam("userIdEmail") String email,
      @RequestParam(value = "userIdBirthday", required = false) String birthdayStr,
      @RequestParam(value = "userIdGender", required = false) String gender,
      @RequestParam(value = "userIdPhoneNumber", required = false) String phoneNumber,
      @RequestParam(value = "userIdAddress", required = false) String address,
      @RequestParam(value = "avatarFile", required = false) MultipartFile avatar,
      @AuthenticationPrincipal CustomUserDetails principal) {
    ApiResult<Void> result =
        apiReaderFacade.updateProfile(
            username, email, birthdayStr, gender, phoneNumber, address, avatar, principal);
    return buildResponse(result);
  }

  @PostMapping("/secure/change-password")
  @PreAuthorize("hasRole('READER')")
  public ResponseEntity<ApiResponse<Void>> changePassword(
      @RequestBody Map<String, String> params,
      @AuthenticationPrincipal CustomUserDetails principal) {
    ApiResult<Void> result = apiReaderFacade.changePassword(params, principal);
    return buildResponse(result);
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
