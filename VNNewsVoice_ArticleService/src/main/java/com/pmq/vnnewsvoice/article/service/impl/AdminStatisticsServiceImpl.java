package com.pmq.vnnewsvoice.article.service.impl;

import com.pmq.vnnewsvoice.article.dto.AdminDashboardStatisticsResponse;
import com.pmq.vnnewsvoice.article.enums.ArticleStatus;
import com.pmq.vnnewsvoice.article.repository.ArticleLikeRepository;
import com.pmq.vnnewsvoice.article.repository.ArticleRepository;
import com.pmq.vnnewsvoice.article.repository.CategoryRepository;
import com.pmq.vnnewsvoice.article.repository.GeneratorRepository;
import com.pmq.vnnewsvoice.article.service.AdminStatisticsService;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Date;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class AdminStatisticsServiceImpl implements AdminStatisticsService {

  private final ArticleRepository articleRepository;
  private final ArticleLikeRepository articleLikeRepository;
  private final CategoryRepository categoryRepository;
  private final GeneratorRepository generatorRepository;

  @Override
  public AdminDashboardStatisticsResponse getDashboardStatistics(int days) {
    Date sevenDaysAgo = Date.from(Instant.now().minus(7, ChronoUnit.DAYS));
    Date thirtyDaysAgo = Date.from(Instant.now().minus(30, ChronoUnit.DAYS));
    Date nDaysAgo = Date.from(Instant.now().minus(days, ChronoUnit.DAYS));

    return AdminDashboardStatisticsResponse.builder()
        // --- Overview counters ---
        .totalArticles(articleRepository.count())
        .totalLikes(articleLikeRepository.count())
        .totalCategories(categoryRepository.count())
        .totalActiveCategories(categoryRepository.countByIsActiveTrue())
        .totalGenerators(generatorRepository.count())
        .totalActiveGenerators(generatorRepository.countByIsActiveTrue())
        // --- Recency counters ---
        .publishedLast7Days(
            articleRepository.countByStatusAndPublishedDateAfter(
                ArticleStatus.PUBLISHED, sevenDaysAgo))
        .publishedLast30Days(
            articleRepository.countByStatusAndPublishedDateAfter(
                ArticleStatus.PUBLISHED, thirtyDaysAgo))
        .publishedLastNDays(
            articleRepository.countByStatusAndPublishedDateAfter(ArticleStatus.PUBLISHED, nDaysAgo))
        // --- Breakdowns ---
        .byStatus(articleRepository.getStatusStatistics())
        .byCategory(articleRepository.getCategoryStatistics())
        .byGenerator(articleRepository.getGeneratorStatistics())
        .build();
  }
}
