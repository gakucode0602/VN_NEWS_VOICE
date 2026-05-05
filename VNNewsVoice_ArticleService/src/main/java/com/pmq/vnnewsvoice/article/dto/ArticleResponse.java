package com.pmq.vnnewsvoice.article.dto;

import java.util.Date;
import java.util.UUID;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ArticleResponse {
  private UUID id;
  private String title;
  private String author;
  private Date publishedDate;
  private String audioUrl;
  private String summary;
  private Boolean isActive;
  private String slug;
  private String originalUrl;
  private Long categoryIdId;
  private String categoryIdName;
  private String topImageUrl;
  private String videoUrl;
  private Boolean isVideoAccepted;
  private Long generatorIdId;
  private String generatorIdName;
  private String generatorIdLogoUrl;
  private String generatorIdUrl;
  // commentCount is null — CommentService not present in ArticleService
  private Long commentCount;
}
