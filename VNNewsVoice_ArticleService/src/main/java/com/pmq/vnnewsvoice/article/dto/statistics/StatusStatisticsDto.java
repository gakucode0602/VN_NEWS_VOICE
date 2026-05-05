package com.pmq.vnnewsvoice.article.dto.statistics;

import com.pmq.vnnewsvoice.article.enums.ArticleStatus;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class StatusStatisticsDto {
  private ArticleStatus status;
  private Long articleCount;
}
