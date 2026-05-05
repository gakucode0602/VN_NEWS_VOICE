package com.pmq.vnnewsvoice.article.mapper;

import com.pmq.vnnewsvoice.article.dto.ArticleLikeDto;
import com.pmq.vnnewsvoice.article.pojo.ArticleLike;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper(componentModel = "spring")
public interface ArticleLikeMapper {

  @Mapping(target = "articleIdId", source = "articleId.id")
  @Mapping(target = "articleIdTitle", source = "articleId.title")
  @Mapping(target = "articleIdSlug", source = "articleId.slug")
  // readerId is already a flat Long storing UserInfo.id — maps directly
  @Mapping(target = "readerId", source = "readerId")
  ArticleLikeDto toDto(ArticleLike articleLike);
}
