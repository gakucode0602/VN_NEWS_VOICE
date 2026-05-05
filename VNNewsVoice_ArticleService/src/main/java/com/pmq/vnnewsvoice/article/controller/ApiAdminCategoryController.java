package com.pmq.vnnewsvoice.article.controller;

import com.pmq.vnnewsvoice.article.dto.ApiResponse;
import com.pmq.vnnewsvoice.article.dto.ApiResult;
import com.pmq.vnnewsvoice.article.dto.CategoryDto;
import com.pmq.vnnewsvoice.article.dto.CategoryListResponse;
import com.pmq.vnnewsvoice.article.dto.CategoryRequest;
import com.pmq.vnnewsvoice.article.facade.ApiAdminCategoryFacade;
import jakarta.validation.Valid;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/secure/admin/categories")
@PreAuthorize("hasRole('ADMIN')")
public class ApiAdminCategoryController {

  private final ApiAdminCategoryFacade facade;

  @GetMapping
  public ResponseEntity<ApiResponse<CategoryListResponse>> getCategories(
      @RequestParam(required = false) Map<String, String> params) {
    ApiResult<CategoryListResponse> res = facade.getCategories(params);
    return buildResponse(res);
  }

  @PostMapping
  public ResponseEntity<ApiResponse<CategoryDto>> addCategory(
      @RequestBody @Valid CategoryRequest req) {
    ApiResult<CategoryDto> res = facade.addCategory(req);
    return buildResponse(res);
  }

  @PutMapping("/{id}")
  public ResponseEntity<ApiResponse<CategoryDto>> updateCategory(
      @PathVariable Long id, @RequestBody @Valid CategoryRequest req) {
    ApiResult<CategoryDto> res = facade.updateCategory(id, req);
    return buildResponse(res);
  }

  @PutMapping("/{id}/status")
  public ResponseEntity<ApiResponse<Void>> toggleStatus(@PathVariable Long id) {
    ApiResult<Void> res = facade.toggleCategoryStatus(id);
    return buildResponse(res);
  }

  @DeleteMapping("/{id}")
  public ResponseEntity<ApiResponse<Void>> deleteCategory(@PathVariable Long id) {
    ApiResult<Void> res = facade.deleteCategory(id);
    return buildResponse(res);
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
