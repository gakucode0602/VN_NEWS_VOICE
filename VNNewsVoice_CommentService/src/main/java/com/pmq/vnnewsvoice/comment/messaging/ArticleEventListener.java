package com.pmq.vnnewsvoice.comment.messaging;

import com.pmq.vnnewsvoice.comment.config.RabbitMQConfig;
import com.pmq.vnnewsvoice.comment.dto.amqp.ArticleEventMessage;
import com.pmq.vnnewsvoice.comment.service.CommentService;
import java.util.Locale;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

@Component
@RequiredArgsConstructor
@Slf4j
public class ArticleEventListener {

  private final CommentService commentService;

  @RabbitListener(queues = RabbitMQConfig.COMMENT_SERVICE_QUEUE)
  public void onArticleEvent(ArticleEventMessage event) {
    if (event == null || !StringUtils.hasText(event.getArticleId())) {
      log.warn("[AMQP] Skip article.events without articleId");
      return;
    }

    String eventType = event.getEventType() != null ? event.getEventType().toLowerCase() : "";

    if ("article.delete".equals(eventType) || "article.deleted".equals(eventType)) {
      int affected = commentService.hardDeleteCommentsByArticleId(event.getArticleId());
      log.info("[AMQP] Hard-deleted {} comments for article {}", affected, event.getArticleId());
      return;
    }

    if (!"article.updated".equals(eventType)) {
      log.debug(
          "[AMQP] Skip non-updated event: type={} articleId={}",
          event.getEventType(),
          event.getArticleId());
      return;
    }

    String status =
        event.getStatus() != null ? event.getStatus().trim().toUpperCase(Locale.ROOT) : "";

    if ("DELETED".equals(status)) {
      int affected = commentService.hideCommentsByArticleId(event.getArticleId());
      log.info("[AMQP] Hid {} comments for deleted article {}", affected, event.getArticleId());
      return;
    }

    if ("PUBLISHED".equals(status) && !Boolean.FALSE.equals(event.getIsActive())) {
      int affected = commentService.restoreCommentsByArticleId(event.getArticleId());
      log.info("[AMQP] Restored {} comments for article {}", affected, event.getArticleId());
      return;
    }

    log.debug(
        "[AMQP] Skip article.updated because status is not PUBLISHED/DELETED: articleId={} status={} isActive={}",
        event.getArticleId(),
        event.getStatus(),
        event.getIsActive());
  }
}
