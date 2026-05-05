package com.pmq.vnnewsvoice.scheduler.scheduler;

import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.pmq.vnnewsvoice.scheduler.config.CrawlSourcesConfig;
import com.pmq.vnnewsvoice.scheduler.config.CrawlSourcesConfig.CrawlSource;
import com.pmq.vnnewsvoice.scheduler.service.CrawlPublisherService;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

class CrawlSchedulerTest {

  @Test
  void shouldSkipPublishingWhenSchedulingDisabled() {
    CrawlPublisherService publisherService = mock(CrawlPublisherService.class);
    CrawlSourcesConfig sourcesConfig = mock(CrawlSourcesConfig.class);
    CrawlScheduler scheduler = new CrawlScheduler(publisherService, sourcesConfig);

    ReflectionTestUtils.setField(scheduler, "schedulingEnabled", false);
    scheduler.scheduleCrawlTasks();

    verify(publisherService, never()).publishCrawlTask(org.mockito.ArgumentMatchers.any());
  }

  @Test
  void shouldPublishAllConfiguredSourcesWhenEnabled() {
    CrawlPublisherService publisherService = mock(CrawlPublisherService.class);
    CrawlSourcesConfig sourcesConfig = mock(CrawlSourcesConfig.class);
    CrawlScheduler scheduler = new CrawlScheduler(publisherService, sourcesConfig);

    CrawlSource first = new CrawlSource("vnexpress", "VnExpress", "https://vnexpress.net");
    CrawlSource second = new CrawlSource("dantri", "Dan Tri", "https://dantri.com.vn");
    when(sourcesConfig.getSources()).thenReturn(List.of(first, second));

    ReflectionTestUtils.setField(scheduler, "schedulingEnabled", true);
    scheduler.scheduleCrawlTasks();

    verify(publisherService).publishCrawlTask(first);
    verify(publisherService).publishCrawlTask(second);
  }

  @Test
  void shouldContinuePublishingWhenOneSourceFails() {
    CrawlPublisherService publisherService = mock(CrawlPublisherService.class);
    CrawlSourcesConfig sourcesConfig = mock(CrawlSourcesConfig.class);
    CrawlScheduler scheduler = new CrawlScheduler(publisherService, sourcesConfig);

    CrawlSource first = new CrawlSource("vnexpress", "VnExpress", "https://vnexpress.net");
    CrawlSource second = new CrawlSource("dantri", "Dan Tri", "https://dantri.com.vn");
    when(sourcesConfig.getSources()).thenReturn(List.of(first, second));
    doThrow(new RuntimeException("boom")).when(publisherService).publishCrawlTask(first);

    ReflectionTestUtils.setField(scheduler, "schedulingEnabled", true);
    scheduler.scheduleCrawlTasks();

    verify(publisherService).publishCrawlTask(first);
    verify(publisherService).publishCrawlTask(second);
  }
}
