package com.pmq.vnnewsvoice.article.repository;

import com.pmq.vnnewsvoice.article.pojo.Category;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

public interface CategoryRepository
    extends JpaRepository<Category, Long>, JpaSpecificationExecutor<Category> {

  long countByIsActiveTrue();
}
