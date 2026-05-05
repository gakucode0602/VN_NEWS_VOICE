package com.pmq.vnnewsvoice.article.service.impl;

import com.pmq.vnnewsvoice.article.pojo.Category;
import com.pmq.vnnewsvoice.article.repository.CategoryRepository;
import com.pmq.vnnewsvoice.article.repository.RepositoryPageable;
import com.pmq.vnnewsvoice.article.repository.specification.CategorySpecifications;
import com.pmq.vnnewsvoice.article.service.CategoryService;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class CategoryServiceImpl implements CategoryService {
  private final CategoryRepository categoryRepository;

  @Override
  @Transactional
  public Category addCategory(Category category) {
    return categoryRepository.save(category);
  }

  @Override
  public Optional<Category> getCategoryById(Long id) {
    return categoryRepository.findById(id);
  }

  @Override
  public List<Category> getCategories(Map<String, String> params) {
    Specification<Category> spec = CategorySpecifications.fromFilters(params);
    return RepositoryPageable.fromParams(params, 20, Sort.by("id").ascending())
        .map(pageable -> (List<Category>) categoryRepository.findAll(spec, pageable).getContent())
        .orElse(categoryRepository.findAll(spec));
  }

  @Override
  @Transactional
  public Category updateCategory(Category category) {
    return categoryRepository.save(category);
  }

  @Override
  @Transactional
  public boolean deleteCategory(Long id) {
    if (id == null || !categoryRepository.existsById(id)) {
      return false;
    }
    categoryRepository.deleteById(id);
    return true;
  }

  @Override
  public long countCategories(Map<String, String> params) {
    Specification<Category> spec = CategorySpecifications.fromFilters(params);
    return categoryRepository.count(spec);
  }

  @Override
  public long countSearchCategories(Map<String, String> params) {
    Specification<Category> spec = CategorySpecifications.fromFilters(params);
    return categoryRepository.count(spec);
  }
}
