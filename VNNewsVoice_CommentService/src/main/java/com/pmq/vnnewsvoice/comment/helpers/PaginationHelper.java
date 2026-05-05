package com.pmq.vnnewsvoice.comment.helpers;

import com.pmq.vnnewsvoice.comment.dto.Pagination;
import java.util.Map;
import org.springframework.stereotype.Component;

@Component
public class PaginationHelper {

  private static final int DEFAULT_PAGE = 1;

  public Pagination createPagination(
      Map<String, String> params, long totalElements, int defaultSize) {
    int size = defaultSize;
    int page = DEFAULT_PAGE;

    if (params != null) {
      if (params.containsKey("size")) {
        try {
          size = Integer.parseInt(params.get("size"));
          if (size <= 0) size = defaultSize;
        } catch (NumberFormatException ignored) {
        }
      }
      if (params.containsKey("page")) {
        try {
          page = Integer.parseInt(params.get("page"));
          if (page <= 0) page = DEFAULT_PAGE;
        } catch (NumberFormatException ignored) {
        }
      }
    }

    int totalPages = size > 0 ? (int) Math.ceil((double) totalElements / size) : 0;

    return new Pagination(page, size, totalElements, totalPages, page < totalPages, page > 1);
  }
}
