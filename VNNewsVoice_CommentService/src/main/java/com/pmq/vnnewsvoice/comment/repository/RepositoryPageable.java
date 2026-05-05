package com.pmq.vnnewsvoice.comment.repository;

import java.util.Map;
import java.util.Optional;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;

public class RepositoryPageable {

  private static final int DEFAULT_PAGE = 0; // JPA 0-indexed

  public static Optional<Pageable> fromParams(
      Map<String, String> params, int defaultSize, Sort sort) {
    if (params == null || params.isEmpty()) {
      return Optional.empty();
    }

    int size = defaultSize;
    int page = DEFAULT_PAGE;

    if (params.containsKey("size")) {
      try {
        size = Integer.parseInt(params.get("size"));
        if (size <= 0) size = defaultSize;
      } catch (NumberFormatException ignored) {
      }
    }
    if (params.containsKey("page")) {
      try {
        // Convert 1-indexed (from client) to 0-indexed (JPA)
        page = Math.max(0, Integer.parseInt(params.get("page")) - 1);
      } catch (NumberFormatException ignored) {
      }
    }

    return Optional.of(PageRequest.of(page, size, sort));
  }
}
