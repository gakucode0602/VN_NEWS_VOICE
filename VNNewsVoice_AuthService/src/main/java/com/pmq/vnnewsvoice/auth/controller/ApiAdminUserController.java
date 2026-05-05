package com.pmq.vnnewsvoice.auth.controller;

import com.pmq.vnnewsvoice.auth.dto.ApiResponse;
import com.pmq.vnnewsvoice.auth.dto.ApiResult;
import com.pmq.vnnewsvoice.auth.dto.UpdateRoleRequest;
import com.pmq.vnnewsvoice.auth.dto.UserListResponse;
import com.pmq.vnnewsvoice.auth.facade.ApiAdminUserFacade;
import jakarta.validation.Valid;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/secure/admin/users")
@PreAuthorize("hasRole('ADMIN')")
public class ApiAdminUserController {

  private final ApiAdminUserFacade apiAdminUserFacade;

  @GetMapping
  public ResponseEntity<ApiResponse<UserListResponse>> getUsers(
      @RequestParam(required = false) Map<String, String> params) {
    ApiResult<UserListResponse> result = apiAdminUserFacade.getUsers(params);
    return buildResponse(result);
  }

  @PutMapping("/{id}/status")
  public ResponseEntity<ApiResponse<Void>> toggleStatus(@PathVariable Long id) {
    ApiResult<Void> result = apiAdminUserFacade.toggleUserStatus(id);
    return buildResponse(result);
  }

  @PutMapping("/{id}/roles")
  public ResponseEntity<ApiResponse<Void>> updateRoles(
      @PathVariable Long id, @RequestBody @Valid UpdateRoleRequest req) {
    ApiResult<Void> result = apiAdminUserFacade.updateUserRole(id, req.getRoleName());
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
