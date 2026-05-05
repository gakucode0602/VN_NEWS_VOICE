package com.pmq.vnnewsvoice.scheduler.config;

import org.springframework.amqp.core.Binding;
import org.springframework.amqp.core.BindingBuilder;
import org.springframework.amqp.core.DirectExchange;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.core.QueueBuilder;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * RabbitMQ topology for SchedulerService. This service is a PUBLISHER only — it declares the queue
 * so it exists before Crawling Service starts. Crawling Service (Phase 1.2) will be the consumer.
 *
 * <p>Queue topology: SchedulerService ──publishes──▶ [crawl.task] ──delivers──▶ CrawlingService
 */
@Configuration
public class RabbitMQConfig {

  /** Name of the queue SchedulerService publishes crawl tasks to. */
  public static final String CRAWL_TASK_QUEUE = "crawl.task";

  public static final String CRAWL_TASK_DLX_EXCHANGE = "crawl.task.dlx";
  public static final String CRAWL_TASK_DLQ = "crawl.task.dlq";
  public static final String CRAWL_TASK_DLQ_ROUTING_KEY = "crawl.task.failed";

  @Bean
  public DirectExchange crawlTaskDlxExchange() {
    return new DirectExchange(CRAWL_TASK_DLX_EXCHANGE, true, false);
  }

  @Bean
  public Queue crawlTaskDlqQueue() {
    return QueueBuilder.durable(CRAWL_TASK_DLQ).build();
  }

  @Bean
  public Binding crawlTaskDlqBinding(Queue crawlTaskDlqQueue, DirectExchange crawlTaskDlxExchange) {
    return BindingBuilder.bind(crawlTaskDlqQueue)
        .to(crawlTaskDlxExchange)
        .with(CRAWL_TASK_DLQ_ROUTING_KEY);
  }

  @Bean
  public Queue crawlTaskQueue() {
    // Keep declaration arguments identical to consumer side to avoid PRECONDITION_FAILED.
    return QueueBuilder.durable(CRAWL_TASK_QUEUE)
        .deadLetterExchange(CRAWL_TASK_DLX_EXCHANGE)
        .deadLetterRoutingKey(CRAWL_TASK_DLQ_ROUTING_KEY)
        .build();
  }

  /** Use Jackson for JSON serialization/deserialization of message payloads. */
  @Bean
  public MessageConverter jsonMessageConverter() {
    return new Jackson2JsonMessageConverter();
  }
}
