package com.pmq.vnnewsvoice.scheduler.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;

import com.pmq.vnnewsvoice.scheduler.config.CrawlSourcesConfig.CrawlSource;
import com.pmq.vnnewsvoice.scheduler.config.RabbitMQConfig;
import com.pmq.vnnewsvoice.scheduler.dto.CrawlTaskMessage;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.amqp.rabbit.core.RabbitTemplate;

class CrawlPublisherServiceTest {

  @Test
  void publishCrawlTaskShouldSendExpectedMessage() {
    RabbitTemplate rabbitTemplate = mock(RabbitTemplate.class);
    CrawlPublisherService service = new CrawlPublisherService(rabbitTemplate);

    CrawlSource source = new CrawlSource("vnexpress", "VnExpress", "https://vnexpress.net");
    service.publishCrawlTask(source);

    ArgumentCaptor<CrawlTaskMessage> messageCaptor =
        ArgumentCaptor.forClass(CrawlTaskMessage.class);
    verify(rabbitTemplate)
        .convertAndSend(eq(RabbitMQConfig.CRAWL_TASK_QUEUE), messageCaptor.capture());

    CrawlTaskMessage message = messageCaptor.getValue();
    assertThat(message.getSourceId()).isEqualTo("vnexpress");
    assertThat(message.getSourceName()).isEqualTo("VnExpress");
    assertThat(message.getBaseUrl()).isEqualTo("https://vnexpress.net");
    assertThat(message.getRequestedAt()).isNotNull();
  }
}
