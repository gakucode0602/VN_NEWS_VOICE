package com.pmq.vnnewsvoice.article.facade;

import com.pmq.vnnewsvoice.article.dto.ApiResult;
import com.pmq.vnnewsvoice.article.dto.CategoryDto;
import com.pmq.vnnewsvoice.article.dto.CategoryListResponse;
import com.pmq.vnnewsvoice.article.dto.CategoryRequest;
import java.util.Map;

public interface ApiAdminCategoryFacade {
  ApiResult<CategoryListResponse> getCategories(Map<String, String> params);

  ApiResult<CategoryDto> addCategory(CategoryRequest request);

  ApiResult<CategoryDto> updateCategory(Long id, CategoryRequest request);

  ApiResult<Void> toggleCategoryStatus(Long id);

  ApiResult<Void> deleteCategory(Long id);
}
