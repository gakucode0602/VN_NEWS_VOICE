package com.pmq.vnnewsvoice.article.dto;

import com.pmq.vnnewsvoice.article.dto.statistics.CategoryStatisticsDto;
import com.pmq.vnnewsvoice.article.dto.statistics.GeneratorStatisticsDto;
import com.pmq.vnnewsvoice.article.dto.statistics.StatusStatisticsDto;
import java.util.List;
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
public class AdminDashboardStatisticsResponse {

  // --- Overview counters ---
  private Long totalArticles;
  private Long totalLikes;
  private Long totalActiveCategories;
  private Long totalCategories;
  private Long totalActiveGenerators;
  private Long totalGenerators;

  // --- Recency counters ---
  private Long publishedLast7Days;
  private Long publishedLast30Days;
  private Long publishedLastNDays;

  // --- Breakdowns ---
  private List<StatusStatisticsDto> byStatus;
  private List<CategoryStatisticsDto> byCategory;
  private List<GeneratorStatisticsDto> byGenerator;
}
