package com.pmq.vnnewsvoice.article.repository;

import java.util.Map;
import java.util.Optional;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;

public final class RepositoryPageable {
  private RepositoryPageable() {}

  public static Optional<Pageable> fromParams(
      Map<String, String> params, int defaultPageSize, Sort sort) {
    if (params == null) {
      return Optional.empty();
    }

    int page = Integer.parseInt(params.getOrDefault("page", "1"));
    int pageSize =
        Integer.parseInt(params.getOrDefault("pageSize", String.valueOf(defaultPageSize)));
    page = Math.max(1, page);
    if (pageSize <= 0) {
      pageSize = defaultPageSize;
    }

    Sort resolvedSort = sort == null ? Sort.unsorted() : sort;
    return Optional.of(PageRequest.of(page - 1, pageSize, resolvedSort));
  }
}
