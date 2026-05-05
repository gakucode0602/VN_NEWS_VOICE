package com.pmq.vnnewsvoice.article.repository.specification;

import com.pmq.vnnewsvoice.article.pojo.Article;
import jakarta.persistence.criteria.Predicate;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import org.springframework.data.jpa.domain.Specification;

public final class ArticleSpecifications {
  private ArticleSpecifications() {}

  public static Specification<Article> fromFilters(Map<String, String> filters) {
    return (root, query, builder) -> {
      List<Predicate> predicates = new ArrayList<>();

      if (filters != null) {

        if (filters.containsKey("categoryId") && !filters.get("categoryId").isEmpty()) {
          String categoryIdStr = filters.get("categoryId");
          Long categoryId = Long.parseLong(categoryIdStr);
          predicates.add(builder.equal(root.get("categoryId").get("id"), categoryId));
        }

        if (filters.containsKey("author") && !filters.get("author").isEmpty()) {
          String author = filters.get("author");
          predicates.add(
              builder.like(builder.lower(root.get("author")), "%" + author.toLowerCase() + "%"));
        }

        if (filters.containsKey("slug")) {
          String slug = filters.get("slug");
          predicates.add(builder.equal(builder.lower(root.get("slug")), slug.toLowerCase()));
        }

        if (filters.containsKey("isActive")) {
          Boolean isActive = Boolean.parseBoolean(filters.get("isActive"));
          predicates.add(builder.equal(root.get("isActive"), isActive));
        }

        if (filters.containsKey("publishedDate")) {
          String publishedDate = filters.get("publishedDate");
          predicates.add(builder.equal(root.get("publishedDate"), publishedDate));
        }

        if (filters.containsKey("generatorId")) {
          String generatorIdStr = filters.get("generatorId");
          if (generatorIdStr != null && !generatorIdStr.isEmpty()) {
            Long generatorId = Long.parseLong(generatorIdStr);
            predicates.add(builder.equal(root.get("generatorId").get("id"), generatorId));
          }
        }

        if (filters.containsKey("fromDate") && filters.containsKey("toDate")) {
          String fromDate = filters.get("fromDate");
          String toDate = filters.get("toDate");
          predicates.add(
              builder.between(
                  root.get("publishedDate"),
                  java.sql.Date.valueOf(fromDate),
                  java.sql.Date.valueOf(toDate)));
        }

        if (filters.containsKey("publishedDates") && !filters.get("publishedDates").isEmpty()) {
          int days = Integer.parseInt(filters.get("publishedDates"));
          Calendar calendar = Calendar.getInstance();
          Date endDate = calendar.getTime();
          calendar.add(Calendar.DAY_OF_YEAR, -days);
          Date startDate = calendar.getTime();
          predicates.add(
              builder.between(
                  root.get("publishedDate"),
                  new java.sql.Date(startDate.getTime()),
                  new java.sql.Date(endDate.getTime())));
        }

        if (filters.containsKey("status") && !filters.get("status").isEmpty()) {
          String status = filters.get("status").trim().toUpperCase(Locale.ROOT);
          if ("DELETE".equals(status)) {
            status = "DELETED";
          }
          predicates.add(builder.equal(root.get("status").as(String.class), status));
        }

        // Support delta sync: articles created on or after the given ISO-8601 instant
        if (filters.containsKey("createdAfter")) {
          String createdAfterStr = filters.get("createdAfter");
          Instant instant = Instant.parse(createdAfterStr);
          predicates.add(builder.greaterThanOrEqualTo(root.get("createdAt"), Date.from(instant)));
        }
      }

      if (predicates.isEmpty()) {
        return null;
      }
      return builder.and(predicates.toArray(new Predicate[0]));
    };
  }
}
