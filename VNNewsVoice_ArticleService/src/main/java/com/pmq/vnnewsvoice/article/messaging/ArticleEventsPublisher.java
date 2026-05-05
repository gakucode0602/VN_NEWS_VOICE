package com.pmq.vnnewsvoice.article.messaging;

import com.pmq.vnnewsvoice.article.config.RabbitMQConfig;
import com.pmq.vnnewsvoice.article.dto.amqp.ArticleEventMessage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
@Slf4j
public class ArticleEventsPublisher {

  private final RabbitTemplate rabbitTemplate;

  public void publishArticleUpdated(ArticleEventMessage event) {
    rabbitTemplate.convertAndSend(RabbitMQConfig.ARTICLE_EVENTS_EXCHANGE, "", event);
    log.info(
        "[AMQP] Published article.events: type={} articleId={} status={}",
        event.getEventType(),
        event.getArticleId(),
        event.getStatus());
  }

  public void publishArticleDeleted(ArticleEventMessage event) {
    rabbitTemplate.convertAndSend(RabbitMQConfig.ARTICLE_EVENTS_EXCHANGE, "", event);
    log.info(
        "[AMQP] Published article.events: type={} articleId={} status={}",
        event.getEventType(),
        event.getArticleId(),
        event.getStatus());
  }
}
