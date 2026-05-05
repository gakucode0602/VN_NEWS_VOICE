package com.pmq.vnnewsvoice.article.scheduler;

import com.pmq.vnnewsvoice.article.dto.amqp.ArticleEventMessage;
import com.pmq.vnnewsvoice.article.enums.ArticleStatus;
import com.pmq.vnnewsvoice.article.messaging.ArticleEventsPublisher;
import com.pmq.vnnewsvoice.article.pojo.Article;
import com.pmq.vnnewsvoice.article.repository.ArticleRepository;
import com.pmq.vnnewsvoice.article.service.ArticleService;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Date;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
@Slf4j
public class ArticleRetentionPurgeScheduler {

  private final ArticleRepository articleRepository;
  private final ArticleService articleService;
  private final ArticleEventsPublisher articleEventsPublisher;

  @Value("${article.lifecycle.purge.enabled:true}")
  private boolean purgeEnabled;

  @Value("${article.lifecycle.purge.retention-days:30}")
  private int retentionDays;

  @Value("${article.lifecycle.purge.batch-size:100}")
  private int batchSize;

  @Scheduled(cron = "${article.lifecycle.purge.cron:0 0 2 * * *}")
  public void purgeDeletedArticles() {
    if (!purgeEnabled) {
      return;
    }

    if (retentionDays < 0) {
      log.warn("[Scheduler] Skip article purge due to negative retentionDays={}", retentionDays);
      return;
    }

    Date cutoff = Date.from(Instant.now().minus(retentionDays, ChronoUnit.DAYS));
    int safeBatchSize = Math.max(1, batchSize);

    List<Article> expiredDeletedArticles =
        articleRepository
            .findByStatusAndDeletedAtBefore(
                ArticleStatus.DELETED,
                cutoff,
                PageRequest.of(0, safeBatchSize, Sort.by(Sort.Direction.ASC, "deletedAt")))
            .getContent();

    if (expiredDeletedArticles.isEmpty()) {
      return;
    }

    int deletedCount = 0;
    int skippedCount = 0;

    for (Article article : expiredDeletedArticles) {
      try {
        boolean deleted = articleService.deleteArticle(article.getId());
        if (!deleted) {
          skippedCount++;
          log.warn(
              "[Scheduler] Skip hard-delete because article was not found: articleId={}",
              article.getId());
          continue;
        }
        deletedCount++;
        try {
          articleEventsPublisher.publishArticleDeleted(buildDeleteEvent(article));
        } catch (Exception publishEx) {
          log.warn(
              "[Scheduler] Article hard-deleted but failed to publish delete event: articleId={}",
              article.getId(),
              publishEx);
        }
      } catch (Exception e) {
        skippedCount++;
        log.error("[Scheduler] Failed to purge deleted article: articleId={}", article.getId(), e);
      }
    }

    log.info(
        "[Scheduler] Article retention purge completed: eligible={} deleted={} skipped={} retentionDays={} cutoff={}",
        expiredDeletedArticles.size(),
        deletedCount,
        skippedCount,
        retentionDays,
        cutoff);
  }

  private ArticleEventMessage buildDeleteEvent(Article article) {
    ArticleEventMessage event = new ArticleEventMessage();
    event.setArticleId(article.getId());
    event.setEventType("article.delete");
    event.setStatus(ArticleStatus.DELETED.name());
    event.setIsActive(false);
    event.setDeletedAt(
        article.getDeletedAt() != null ? article.getDeletedAt().toInstant().toString() : null);
    return event;
  }
}
