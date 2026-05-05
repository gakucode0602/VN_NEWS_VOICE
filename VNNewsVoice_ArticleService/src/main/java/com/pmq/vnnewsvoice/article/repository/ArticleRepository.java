package com.pmq.vnnewsvoice.article.repository;

import com.pmq.vnnewsvoice.article.dto.statistics.CategoryStatisticsDto;
import com.pmq.vnnewsvoice.article.dto.statistics.GeneratorStatisticsDto;
import com.pmq.vnnewsvoice.article.dto.statistics.StatusStatisticsDto;
import com.pmq.vnnewsvoice.article.enums.ArticleStatus;
import com.pmq.vnnewsvoice.article.pojo.Article;
import java.util.Date;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface ArticleRepository
    extends JpaRepository<Article, UUID>, JpaSpecificationExecutor<Article> {

  Optional<Article> findByIdAndStatusAndIsActiveTrue(UUID id, ArticleStatus status);

  List<Article> findByCategoryId_IdAndIsActiveTrueOrderByPublishedDateDesc(Long categoryId);

  Optional<Article> findByOriginalUrl(String originalUrl);

  Page<Article> findByStatusAndDeletedAtBefore(
      ArticleStatus status, Date deletedAt, Pageable pageable);

  // --- Full-Text Search queries ---

  @Query(
      value =
          """
          SELECT a.* FROM article a,
            websearch_to_tsquery('vn_unaccent', :keyword) q
          WHERE a.search_vector @@ q
            AND a.status = 'PUBLISHED'
            AND a.is_active = true
          ORDER BY ts_rank(a.search_vector, q) DESC
          LIMIT :limit OFFSET :offset
          """,
      nativeQuery = true)
  List<Article> fullTextSearch(
      @Param("keyword") String keyword, @Param("limit") int limit, @Param("offset") int offset);

  @Query(
      value =
          """
          SELECT COUNT(*) FROM article a,
            websearch_to_tsquery('vn_unaccent', :keyword) q
          WHERE a.search_vector @@ q
            AND a.status = 'PUBLISHED'
            AND a.is_active = true
          """,
      nativeQuery = true)
  long countFullTextSearch(@Param("keyword") String keyword);

  // --- Statistics queries ---

  @Query(
      "SELECT new com.pmq.vnnewsvoice.article.dto.statistics.CategoryStatisticsDto(c.name, COUNT(a.id)) "
          + "FROM Category c JOIN Article a ON c.id = a.categoryId.id "
          + "GROUP BY c.name ORDER BY COUNT(a.id) DESC")
  List<CategoryStatisticsDto> getCategoryStatistics();

  @Query(
      "SELECT new com.pmq.vnnewsvoice.article.dto.statistics.GeneratorStatisticsDto(g.name, COUNT(a.id)) "
          + "FROM Generator g JOIN Article a ON g.id = a.generatorId.id "
          + "GROUP BY g.id, g.name ORDER BY COUNT(a.id) DESC")
  List<GeneratorStatisticsDto> getGeneratorStatistics();

  @Query(
      "SELECT new com.pmq.vnnewsvoice.article.dto.statistics.StatusStatisticsDto(a.status, COUNT(a.id)) "
          + "FROM Article a GROUP BY a.status")
  List<StatusStatisticsDto> getStatusStatistics();

  @Query(
      "SELECT COUNT(a.id) FROM Article a "
          + "WHERE a.status = :status AND a.publishedDate >= :since")
  Long countByStatusAndPublishedDateAfter(
      @Param("status") ArticleStatus status, @Param("since") Date since);
}
