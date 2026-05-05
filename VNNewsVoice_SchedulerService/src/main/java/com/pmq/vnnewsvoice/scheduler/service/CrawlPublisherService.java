package com.pmq.vnnewsvoice.scheduler.service;

import com.pmq.vnnewsvoice.scheduler.config.CrawlSourcesConfig.CrawlSource;
import com.pmq.vnnewsvoice.scheduler.config.RabbitMQConfig;
import com.pmq.vnnewsvoice.scheduler.dto.CrawlTaskMessage;
import java.time.Instant;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Service;

/**
 * Publishes CrawlTaskMessage to RabbitMQ queue "crawl.task". CrawlingService (Phase 1.2) is the
 * consumer.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class CrawlPublisherService {

  private final RabbitTemplate rabbitTemplate;

  /**
   * Publishes a single crawl task for the given source. Uses the Jackson2JsonMessageConverter
   * configured in RabbitMQConfig.
   */
  public void publishCrawlTask(CrawlSource source) {
    CrawlTaskMessage message =
        CrawlTaskMessage.builder()
            .sourceId(source.getId())
            .sourceName(source.getName())
            .baseUrl(source.getBaseUrl())
            .requestedAt(Instant.now())
            .build();

    rabbitTemplate.convertAndSend(RabbitMQConfig.CRAWL_TASK_QUEUE, message);
    log.info("Published crawl task: sourceId={}, url={}", source.getId(), source.getBaseUrl());
  }
}
