package com.pmq.vnnewsvoice.article.repository.specification;

import com.pmq.vnnewsvoice.article.pojo.Generator;
import jakarta.persistence.criteria.Predicate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.springframework.data.jpa.domain.Specification;

public final class GeneratorSpecifications {
  private GeneratorSpecifications() {}

  public static Specification<Generator> fromFilters(Map<String, String> filters) {
    return (root, query, builder) -> {
      List<Predicate> predicates = new ArrayList<>();

      if (filters != null) {
        if (filters.containsKey("name")) {
          String name = filters.get("name");
          predicates.add(builder.like(root.get("name"), "%" + name + "%"));
        }
        if (filters.containsKey("isActive")) {
          Boolean isActive = Boolean.parseBoolean(filters.get("isActive"));
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
