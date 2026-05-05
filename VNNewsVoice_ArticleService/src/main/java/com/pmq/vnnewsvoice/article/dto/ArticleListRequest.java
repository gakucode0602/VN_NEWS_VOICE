package com.pmq.vnnewsvoice.article.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ArticleListRequest {
  private String name;
  private Long categoryId;
  private Long generatorId;
  private Integer page;
  private String fromDate;
  private String toDate;
  private Integer publishedDates;
}
