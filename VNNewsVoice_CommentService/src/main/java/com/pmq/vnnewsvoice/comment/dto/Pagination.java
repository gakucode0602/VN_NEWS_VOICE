package com.pmq.vnnewsvoice.comment.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class Pagination {
  private int currentPage;
  private int pageSize;
  private long totalItems;
  private int totalPages;
  private boolean hasNext;
  private boolean hasPrevious;
}
