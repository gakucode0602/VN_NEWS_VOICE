package com.pmq.vnnewsvoice.auth.repository.specification;

import com.pmq.vnnewsvoice.auth.pojo.UserInfo;
import jakarta.persistence.criteria.Predicate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.springframework.data.jpa.domain.Specification;

public final class UserInfoSpecifications {
  private UserInfoSpecifications() {}

  public static Specification<UserInfo> fromFilters(Map<String, String> filters) {
    return (root, query, builder) -> {
      List<Predicate> predicates = new ArrayList<>();

      if (filters != null && !filters.isEmpty()) {
        if (filters.containsKey("username")) {
          String keyword =
              "%" + filters.get("username").replace("_", "\\_").replace("%", "\\%") + "%";
          predicates.add(builder.like(root.get("username"), keyword, '\\'));
        }

        if (filters.containsKey("email")) {
          String keyword = "%" + filters.get("email").replace("_", "\\_").replace("%", "\\%") + "%";
          predicates.add(builder.like(root.get("email"), keyword, '\\'));
        }

        if (filters.containsKey("search")) {
          String keyword = "%" + filters.get("search").toLowerCase().trim() + "%";
          Predicate usernamePred = builder.like(builder.lower(root.get("username")), keyword);
          Predicate emailPred = builder.like(builder.lower(root.get("email")), keyword);
          predicates.add(builder.or(usernamePred, emailPred));
        }

        if (filters.containsKey("isActive")) {
          Boolean isActive = Boolean.parseBoolean(filters.get("isActive"));
          predicates.add(builder.equal(root.get("isActive"), isActive));
        }

        if (filters.containsKey("role")) {
          if (!"all".equals(filters.get("role"))) {
            predicates.add(builder.equal(root.get("roleId").get("name"), filters.get("role")));
          }
        }

        if (filters.containsKey("roleFilter")) {
          String[] roles = filters.get("roleFilter").split(",");
          List<Predicate> rolePredicates = new ArrayList<>();
          for (String role : roles) {
            rolePredicates.add(
                builder.equal(root.get("roleId").get("name"), "ROLE_" + role.trim()));
          }
          if (!rolePredicates.isEmpty()) {
            predicates.add(builder.or(rolePredicates.toArray(new Predicate[0])));
          }
        }
      }

      if (predicates.isEmpty()) {
        return null;
      }
      return builder.and(predicates.toArray(new Predicate[0]));
    };
  }
}
