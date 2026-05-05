package com.pmq.vnnewsvoice.comment.config;

import org.springframework.amqp.core.Binding;
import org.springframework.amqp.core.BindingBuilder;
import org.springframework.amqp.core.FanoutExchange;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.rabbit.config.SimpleRabbitListenerContainerFactory;
import org.springframework.amqp.rabbit.connection.ConnectionFactory;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitMQConfig {

  public static final String ARTICLE_EVENTS_EXCHANGE = "article.events";
  public static final String COMMENT_SERVICE_QUEUE = "article.events.comment-service";

  public static final String USER_EVENTS_EXCHANGE = "user.events";
  public static final String USER_EVENTS_COMMENT_QUEUE = "user.events.comment-service";

  @Bean
  public FanoutExchange articleEventsExchange() {
    return new FanoutExchange(ARTICLE_EVENTS_EXCHANGE, true, false);
  }

  @Bean
  public Queue commentServiceQueue() {
    return new Queue(COMMENT_SERVICE_QUEUE, true);
  }

  @Bean
  public Binding commentServiceBinding(
      Queue commentServiceQueue, FanoutExchange articleEventsExchange) {
    return BindingBuilder.bind(commentServiceQueue).to(articleEventsExchange);
  }

  @Bean
  public FanoutExchange userEventsExchange() {
    return new FanoutExchange(USER_EVENTS_EXCHANGE, true, false);
  }

  @Bean
  public Queue userEventsCommentQueue() {
    return new Queue(USER_EVENTS_COMMENT_QUEUE, true);
  }

  @Bean
  public Binding userEventsCommentBinding(
      Queue userEventsCommentQueue, FanoutExchange userEventsExchange) {
    return BindingBuilder.bind(userEventsCommentQueue).to(userEventsExchange);
  }

  @Bean
  public MessageConverter jsonMessageConverter() {
    return new Jackson2JsonMessageConverter();
  }

  @Bean
  public SimpleRabbitListenerContainerFactory rabbitListenerContainerFactory(
      ConnectionFactory connectionFactory) {
    SimpleRabbitListenerContainerFactory factory = new SimpleRabbitListenerContainerFactory();
    factory.setConnectionFactory(connectionFactory);
    factory.setMessageConverter(jsonMessageConverter());
    factory.setPrefetchCount(10);
    return factory;
  }
}
