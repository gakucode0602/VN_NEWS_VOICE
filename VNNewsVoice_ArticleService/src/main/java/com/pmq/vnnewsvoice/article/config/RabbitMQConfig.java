package com.pmq.vnnewsvoice.article.config;

import org.springframework.amqp.core.Binding;
import org.springframework.amqp.core.BindingBuilder;
import org.springframework.amqp.core.FanoutExchange;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.rabbit.config.SimpleRabbitListenerContainerFactory;
import org.springframework.amqp.rabbit.connection.ConnectionFactory;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * RabbitMQ configuration for ArticleService.
 *
 * <p>Declares:
 *
 * <ul>
 *   <li>Fanout exchange {@code article.events}
 *   <li>Durable queue {@code article.events.article-service}
 *   <li>Binding: queue → exchange
 * </ul>
 *
 * <p>Infrastructure is idempotent — safe to run if already declared by MLService.
 */
@Configuration
public class RabbitMQConfig {

  public static final String ARTICLE_EVENTS_EXCHANGE = "article.events";
  public static final String ARTICLE_SERVICE_QUEUE = "article.events.article-service";
  public static final String ML_VIDEO_TASKS_QUEUE = "ml.video.tasks";

  @Bean
  public Queue mlVideoTasksQueue() {
    return new Queue(ML_VIDEO_TASKS_QUEUE, true); // durable — survives broker restart
  }

  @Bean
  public FanoutExchange articleEventsExchange() {
    return new FanoutExchange(ARTICLE_EVENTS_EXCHANGE, true, false);
  }

  @Bean
  public Queue articleServiceQueue() {
    return new Queue(ARTICLE_SERVICE_QUEUE, true); // durable
  }

  @Bean
  public Binding articleServiceBinding(
      Queue articleServiceQueue, FanoutExchange articleEventsExchange) {
    return BindingBuilder.bind(articleServiceQueue).to(articleEventsExchange);
  }

  @Bean
  public MessageConverter jsonMessageConverter() {
    return new Jackson2JsonMessageConverter();
  }

  @Bean
  public RabbitTemplate rabbitTemplate(ConnectionFactory connectionFactory) {
    RabbitTemplate template = new RabbitTemplate(connectionFactory);
    template.setMessageConverter(jsonMessageConverter());
    return template;
  }

  @Bean
  public SimpleRabbitListenerContainerFactory rabbitListenerContainerFactory(
      ConnectionFactory connectionFactory) {
    SimpleRabbitListenerContainerFactory factory = new SimpleRabbitListenerContainerFactory();
    factory.setConnectionFactory(connectionFactory);
    factory.setMessageConverter(jsonMessageConverter());
    factory.setPrefetchCount(1); // 1 at a time — DB upsert can be slow
    return factory;
  }
}
