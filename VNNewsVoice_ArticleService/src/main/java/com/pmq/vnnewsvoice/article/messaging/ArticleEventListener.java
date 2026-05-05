package com.pmq.vnnewsvoice.article.messaging;

import com.pmq.vnnewsvoice.article.config.RabbitMQConfig;
import com.pmq.vnnewsvoice.article.dto.amqp.ArticleEventMessage;
import com.pmq.vnnewsvoice.article.service.ArticleEventService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;

/**
 * @RabbitListener that consumes from queue 'article.events.article-service'. Queue is bound to
 * fanout exchange 'article.events' (see RabbitMQConfig).
 *
 * <p>Spring AMQP auto-converts JSON → ArticleEventMessage via Jackson2JsonMessageConverter. ACK on
 * success, NACK+requeue on exception (configured via SimpleRabbitListenerContainerFactory).
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class ArticleEventListener {

  private final ArticleEventService articleEventService;

  @RabbitListener(queues = RabbitMQConfig.ARTICLE_SERVICE_QUEUE)
  public void onArticleEvent(ArticleEventMessage event) {
    log.info(
        "[AMQP] Received article.events: type={} source={} url={}",
        event.getEventType(),
        event.getSourceId(),
        event.getUrl());

    if ("video.generated".equals(event.getEventType())) {
      try {
        articleEventService.handleVideoGenerated(event);
      } catch (Exception e) {
        log.error(
            "[AMQP] Failed to process video.generated for articleId={}: {}",
            event.getArticleId(),
            e.getMessage(),
            e);
        throw e;
      }
      return;
    }

    if (event.getEventType() != null && !"article.created".equals(event.getEventType())) {
      log.info(
          "[AMQP] Skip non-created event on ArticleService queue: type={} articleId={}",
          event.getEventType(),
          event.getArticleId());
      return;
    }

    try {
      articleEventService.handleArticleCreated(event);
    } catch (Exception e) {
      log.error(
          "[AMQP] Failed to process article event url={}: {}", event.getUrl(), e.getMessage(), e);
      throw e; // re-throw → NACK + requeue
    }
  }
}
