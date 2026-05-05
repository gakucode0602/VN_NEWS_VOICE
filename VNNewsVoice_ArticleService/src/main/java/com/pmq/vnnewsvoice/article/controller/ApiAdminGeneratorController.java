package com.pmq.vnnewsvoice.article.controller;

import com.pmq.vnnewsvoice.article.dto.ApiResponse;
import com.pmq.vnnewsvoice.article.dto.ApiResult;
import com.pmq.vnnewsvoice.article.dto.GeneratorDto;
import com.pmq.vnnewsvoice.article.dto.GeneratorListResponse;
import com.pmq.vnnewsvoice.article.dto.GeneratorRequest;
import com.pmq.vnnewsvoice.article.facade.ApiAdminGeneratorFacade;
import jakarta.validation.Valid;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/secure/admin/generators")
@PreAuthorize("hasRole('ADMIN')")
public class ApiAdminGeneratorController {

  private final ApiAdminGeneratorFacade facade;

  @GetMapping
  public ResponseEntity<ApiResponse<GeneratorListResponse>> getGenerators(
      @RequestParam(required = false) Map<String, String> params) {
    ApiResult<GeneratorListResponse> res = facade.getGenerators(params);
    return buildResponse(res);
  }

  @PostMapping
  public ResponseEntity<ApiResponse<GeneratorDto>> addGenerator(
      @RequestBody @Valid GeneratorRequest req) {
    ApiResult<GeneratorDto> res = facade.addGenerator(req);
    return buildResponse(res);
  }

  @PutMapping("/{id}")
  public ResponseEntity<ApiResponse<GeneratorDto>> updateGenerator(
      @PathVariable Long id, @RequestBody @Valid GeneratorRequest req) {
    ApiResult<GeneratorDto> res = facade.updateGenerator(id, req);
    return buildResponse(res);
  }

  @PutMapping("/{id}/status")
  public ResponseEntity<ApiResponse<Void>> toggleStatus(@PathVariable Long id) {
    ApiResult<Void> res = facade.toggleGeneratorStatus(id);
    return buildResponse(res);
  }

  @DeleteMapping("/{id}")
  public ResponseEntity<ApiResponse<Void>> deleteGenerator(@PathVariable Long id) {
    ApiResult<Void> res = facade.deleteGenerator(id);
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
