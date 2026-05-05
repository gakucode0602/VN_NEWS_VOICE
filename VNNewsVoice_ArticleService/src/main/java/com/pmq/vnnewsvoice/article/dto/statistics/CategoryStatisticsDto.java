package com.pmq.vnnewsvoice.article.dto.statistics;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class CategoryStatisticsDto {
  private String categoryName;
  private Long articleCount;
}
