package com.pmq.vnnewsvoice.article.dto;

import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class GeneratorListResponse {
  private List<GeneratorDto> generators;
  private long totalItems;
  private int currentPage;
  private int totalPages;
  private int startIndex;
  private int endIndex;
}
