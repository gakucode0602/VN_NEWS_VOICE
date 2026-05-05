package com.pmq.vnnewsvoice.article.repository.specification;

import com.pmq.vnnewsvoice.article.pojo.Category;
import jakarta.persistence.criteria.Predicate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.springframework.data.jpa.domain.Specification;

public final class CategorySpecifications {
  private CategorySpecifications() {}

  public static Specification<Category> fromFilters(Map<String, String> filters) {
    return (root, query, builder) -> {
      List<Predicate> predicates = new ArrayList<>();

      if (filters != null) {
        if (filters.containsKey("name")) {
          String name = filters.get("name");
          predicates.add(
              builder.like(builder.lower(root.get("name")), "%" + name.toLowerCase() + "%"));
        }

        if (filters.containsKey("isActive") || filters.containsKey("is_active")) {
          String rawValue = filters.getOrDefault("isActive", filters.get("is_active"));
          boolean isActive = Boolean.parseBoolean(rawValue);
          predicates.add(builder.equal(root.get("isActive"), isActive));
        }
      }

      if (predicates.isEmpty()) {
        return null;
      }
      return builder.and(predicates.toArray(new Predicate[0]));
    };
  }
}
