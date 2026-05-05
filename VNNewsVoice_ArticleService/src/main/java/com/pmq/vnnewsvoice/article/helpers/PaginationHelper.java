package com.pmq.vnnewsvoice.article.helpers;

import com.pmq.vnnewsvoice.article.utils.Pagination;
import java.util.HashMap;
import java.util.Map;
import org.springframework.stereotype.Component;

@Component
public class PaginationHelper {

  public Pagination createPagination(Map<String, String> params, long totalItems, int pageSize) {
    String pageParam = params.getOrDefault("page", "1");
    return new Pagination(pageParam, totalItems, pageSize);
  }

  public Map<String, String> extractFilters(Map<String, String> params, String... filterKeys) {
    Map<String, String> filters = new HashMap<>();
    for (String key : filterKeys) {
      String mappedKey =
          switch (key) {
            case "categoryId" -> "categoryId";
            case "status" -> "status";
            case "search" -> "name";
            case "limit" -> "pageSize";
            default -> key;
          };
      if (params.containsKey(mappedKey)) {
        filters.put(mappedKey, params.get(mappedKey));
      }
    }
    return filters;
  }
}
