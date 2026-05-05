package com.pmq.vnnewsvoice.article.facade.impl;

import com.pmq.vnnewsvoice.article.dto.ApiResult;
import com.pmq.vnnewsvoice.article.dto.CategoryDto;
import com.pmq.vnnewsvoice.article.dto.CategoryListResponse;
import com.pmq.vnnewsvoice.article.dto.CategoryRequest;
import com.pmq.vnnewsvoice.article.facade.ApiAdminCategoryFacade;
import com.pmq.vnnewsvoice.article.mapper.CategoryMapper;
import com.pmq.vnnewsvoice.article.pojo.Category;
import com.pmq.vnnewsvoice.article.service.ArticleService;
import com.pmq.vnnewsvoice.article.service.CategoryService;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class ApiAdminCategoryFacadeImpl implements ApiAdminCategoryFacade {

  private final CategoryService categoryService;
  private final ArticleService articleService;
  private final CategoryMapper categoryMapper;

  @Override
  public ApiResult<CategoryListResponse> getCategories(Map<String, String> params) {
    long totalItems = categoryService.countSearchCategories(params);
    List<Category> list = categoryService.getCategories(params);
    List<CategoryDto> dtos = list.stream().map(categoryMapper::toDto).toList();

    int page = Integer.parseInt(params.getOrDefault("page", "1"));
    int pageSize = Integer.parseInt(params.getOrDefault("pageSize", "10"));
    int totalPages = totalItems == 0 ? 1 : (int) Math.ceil((double) totalItems / pageSize);

    CategoryListResponse res =
        CategoryListResponse.builder()
            .categories(dtos)
            .totalItems(totalItems)
            .currentPage(page)
            .totalPages(totalPages)
            .startIndex(dtos.isEmpty() ? 0 : (page - 1) * pageSize + 1)
            .endIndex(Math.min(page * pageSize, (int) totalItems))
            .build();

    return ApiResult.success(HttpStatus.OK, res);
  }

  @Override
  public ApiResult<CategoryDto> addCategory(CategoryRequest request) {
    Category cat = new Category();
    cat.setName(request.getName());
    cat.setIsActive(request.getIsActive() != null ? request.getIsActive() : true);

    Category saved = categoryService.addCategory(cat);
    if (saved != null) {
      return ApiResult.success(
          HttpStatus.CREATED, categoryMapper.toDto(saved), "Tạo danh mục thành công");
    }
    return ApiResult.failure(HttpStatus.BAD_REQUEST, "Lỗi tạo danh mục");
  }

  @Override
  public ApiResult<CategoryDto> updateCategory(Long id, CategoryRequest request) {
    Optional<Category> opt = categoryService.getCategoryById(id);
    if (opt.isEmpty()) {
      return ApiResult.failure(HttpStatus.NOT_FOUND, "Không tìm thấy danh mục");
    }
    Category cat = opt.get();
    cat.setName(request.getName());
    if (request.getIsActive() != null) {
      cat.setIsActive(request.getIsActive());
    }

    Category updated = categoryService.updateCategory(cat);
    return ApiResult.success(HttpStatus.OK, categoryMapper.toDto(updated), "Cập nhật thành công");
  }

  @Override
  public ApiResult<Void> toggleCategoryStatus(Long id) {
    Optional<Category> opt = categoryService.getCategoryById(id);
    if (opt.isEmpty()) {
      return ApiResult.failure(HttpStatus.NOT_FOUND, "Không tìm thấy danh mục");
    }
    Category cat = opt.get();
    cat.setIsActive(!cat.getIsActive());
    categoryService.updateCategory(cat);
    return ApiResult.success(HttpStatus.OK, null, "Đã cập nhật trạng thái");
  }

  @Override
  public ApiResult<Void> deleteCategory(Long id) {
    Map<String, String> filters = new HashMap<>();
    filters.put("categoryId", id.toString());
    long count = articleService.countSearchArticles(filters);

    if (count > 0) {
      return ApiResult.failure(
          HttpStatus.BAD_REQUEST, "Không thể xóa danh mục đang gắn với bài viết");
    }

    boolean deleted = categoryService.deleteCategory(id);
    if (deleted) {
      return ApiResult.success(HttpStatus.OK, null, "Xóa danh mục thành công");
    }
    return ApiResult.failure(HttpStatus.INTERNAL_SERVER_ERROR, "Lỗi xóa danh mục");
  }
}
