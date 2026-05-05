package com.pmq.vnnewsvoice.article.controller;

import com.pmq.vnnewsvoice.article.dto.ApiResponse;
import com.pmq.vnnewsvoice.article.dto.CategoryDto;
import com.pmq.vnnewsvoice.article.mapper.CategoryMapper;
import com.pmq.vnnewsvoice.article.pojo.Category;
import com.pmq.vnnewsvoice.article.service.CategoryService;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api")
public class ApiCategoryController {
  private final CategoryMapper categoryMapper;
  private final CategoryService categoryService;

  @GetMapping("/categories")
  public ResponseEntity<ApiResponse<List<CategoryDto>>> getCategoryList(
      @RequestParam Map<String, String> params) {
    Map<String, String> filters = new HashMap<>(params);
    // Public endpoint only returns active categories by default.
    filters.putIfAbsent("isActive", "true");

    List<Category> categories = categoryService.getCategories(filters);
    List<CategoryDto> categoryDtos = categories.stream().map(categoryMapper::toDto).toList();
    return ResponseEntity.ok(
        ApiResponse.<List<CategoryDto>>builder()
            .success(true)
            .code(HttpStatus.OK.value())
            .result(categoryDtos)
            .build());
  }
}
