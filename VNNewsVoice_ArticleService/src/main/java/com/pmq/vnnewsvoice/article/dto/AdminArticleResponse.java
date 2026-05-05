package com.pmq.vnnewsvoice.article.dto;

import java.util.Date;
import java.util.UUID;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/** Full article representation for admin — includes internal management fields. */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AdminArticleResponse {
  private UUID id;
  private String title;
  private String author;
  private Date publishedDate;
  private String audioUrl;
  private String summary;
  private Boolean isActive;
  private String slug;
  private String originalUrl;
  private String topImageUrl;
  private String videoUrl;
  private Boolean isVideoAccepted;
  private String status;
  private Date deletedAt;
  private Date createdAt;
  private Date updatedAt;
  private Long categoryIdId;
  private String categoryIdName;
  private Long generatorIdId;
  private String generatorIdName;
  private String generatorIdLogoUrl;
  private String generatorIdUrl;
}
