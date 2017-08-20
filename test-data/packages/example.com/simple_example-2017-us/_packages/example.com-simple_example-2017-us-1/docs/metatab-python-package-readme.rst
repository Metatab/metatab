





<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">



  <link crossorigin="anonymous" href="https://assets-cdn.github.com/assets/frameworks-d7b19415c108234b91acac0d0c02091c860993c13687a757ee345cc1ecd3a9d1.css" media="all" rel="stylesheet" />
  <link crossorigin="anonymous" href="https://assets-cdn.github.com/assets/github-97f8afbdb0a810d4ffa14a5fc7244b862b379d2c341d5eeb89489fbd310e4a83.css" media="all" rel="stylesheet" />
  
  
  <link crossorigin="anonymous" href="https://assets-cdn.github.com/assets/site-537c466d44a69d38c4bd60c2fd2955373ef96d051bd97b2ad30ed039acc97bff.css" media="all" rel="stylesheet" />
  

  <meta name="viewport" content="width=device-width">
  
  <title>metatab-py/README.rst at master · CivicKnowledge/metatab-py · GitHub</title>
  <link rel="search" type="application/opensearchdescription+xml" href="/opensearch.xml" title="GitHub">
  <link rel="fluid-icon" href="https://github.com/fluidicon.png" title="GitHub">
  <meta property="fb:app_id" content="1401488693436528">

    
    <meta content="https://avatars0.githubusercontent.com/u/6617988?v=3&amp;s=400" property="og:image" /><meta content="GitHub" property="og:site_name" /><meta content="object" property="og:type" /><meta content="CivicKnowledge/metatab-py" property="og:title" /><meta content="https://github.com/CivicKnowledge/metatab-py" property="og:url" /><meta content="metatab-py - Python language parser for a tabular format for structured metadata. http://metatab.org" property="og:description" />

  <link rel="assets" href="https://assets-cdn.github.com/">
  
  <meta name="pjax-timeout" content="1000">
  
  <meta name="request-id" content="C5C6:2FBE2:802156:CB895C:59023010" data-pjax-transient>
  

  <meta name="selected-link" value="repo_source" data-pjax-transient>

  <meta name="google-site-verification" content="KT5gs8h0wvaagLKAVWq8bbeNwnZZK1r1XQysX3xurLU">
<meta name="google-site-verification" content="ZzhVyEFwb7w3e0-uOTltm8Jsck2F5StVihD0exw2fsA">
    <meta name="google-analytics" content="UA-3769691-2">

<meta content="collector.githubapp.com" name="octolytics-host" /><meta content="github" name="octolytics-app-id" /><meta content="https://collector.githubapp.com/github-external/browser_event" name="octolytics-event-url" /><meta content="C5C6:2FBE2:802156:CB895C:59023010" name="octolytics-dimension-request_id" />
<meta content="/&lt;user-name&gt;/&lt;repo-name&gt;/blob/show" data-pjax-transient="true" name="analytics-location" />




  <meta class="js-ga-set" name="dimension1" content="Logged Out">


  

      <meta name="hostname" content="github.com">
  <meta name="user-login" content="">

      <meta name="expected-hostname" content="github.com">
    <meta name="js-proxy-site-detection-payload" content="NzI5YzA5ZmFmYzBjNWYzNjBmZDcyYWM1NjU3OWRiMzQyMjQ1MDdkNDRiNTk0MDcxYjgwMzQ1ZDM0MWUwYzYyZnx7InJlbW90ZV9hZGRyZXNzIjoiNzQuNjIuNTEuMiIsInJlcXVlc3RfaWQiOiJDNUM2OjJGQkUyOjgwMjE1NjpDQjg5NUM6NTkwMjMwMTAiLCJ0aW1lc3RhbXAiOjE0OTMzMTU2MDEsImhvc3QiOiJnaXRodWIuY29tIn0=">


  <meta name="html-safe-nonce" content="8cec8abee2a56f5b79f553a1665891a145a83056">

  <meta http-equiv="x-pjax-version" content="b81017741061868db81e0a3db329b50e">
  

    
  <meta name="description" content="metatab-py - Python language parser for a tabular format for structured metadata. http://metatab.org">
  <meta name="go-import" content="github.com/CivicKnowledge/metatab-py git https://github.com/CivicKnowledge/metatab-py.git">

  <meta content="6617988" name="octolytics-dimension-user_id" /><meta content="CivicKnowledge" name="octolytics-dimension-user_login" /><meta content="71386738" name="octolytics-dimension-repository_id" /><meta content="CivicKnowledge/metatab-py" name="octolytics-dimension-repository_nwo" /><meta content="true" name="octolytics-dimension-repository_public" /><meta content="false" name="octolytics-dimension-repository_is_fork" /><meta content="71386738" name="octolytics-dimension-repository_network_root_id" /><meta content="CivicKnowledge/metatab-py" name="octolytics-dimension-repository_network_root_nwo" />
        <link href="https://github.com/CivicKnowledge/metatab-py/commits/master.atom" rel="alternate" title="Recent Commits to metatab-py:master" type="application/atom+xml">


    <link rel="canonical" href="https://github.com/CivicKnowledge/metatab-py/blob/master/README.rst" data-pjax-transient>


  <meta name="browser-stats-url" content="https://api.github.com/_private/browser/stats">

  <meta name="browser-errors-url" content="https://api.github.com/_private/browser/errors">

  <link rel="mask-icon" href="https://assets-cdn.github.com/pinned-octocat.svg" color="#000000">
  <link rel="icon" type="image/x-icon" href="https://assets-cdn.github.com/favicon.ico">

<meta name="theme-color" content="#1e2327">



  </head>

  <body class="logged-out env-production page-blob">
    


  <div class="position-relative js-header-wrapper ">
    <a href="#start-of-content" tabindex="1" class="accessibility-aid js-skip-to-content">Skip to content</a>
    <div id="js-pjax-loader-bar" class="pjax-loader-bar"><div class="progress"></div></div>

    
    
    



          <header class="site-header js-details-container Details" role="banner">
  <div class="container-responsive">
    <a class="header-logo-invertocat" href="https://github.com/" aria-label="Homepage" data-ga-click="(Logged out) Header, go to homepage, icon:logo-wordmark">
      <svg aria-hidden="true" class="octicon octicon-mark-github" height="32" version="1.1" viewBox="0 0 16 16" width="32"><path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>
    </a>

    <button class="btn-link float-right site-header-toggle js-details-target" type="button" aria-label="Toggle navigation">
      <svg aria-hidden="true" class="octicon octicon-three-bars" height="24" version="1.1" viewBox="0 0 12 16" width="18"><path fill-rule="evenodd" d="M11.41 9H.59C0 9 0 8.59 0 8c0-.59 0-1 .59-1H11.4c.59 0 .59.41.59 1 0 .59 0 1-.59 1h.01zm0-4H.59C0 5 0 4.59 0 4c0-.59 0-1 .59-1H11.4c.59 0 .59.41.59 1 0 .59 0 1-.59 1h.01zM.59 11H11.4c.59 0 .59.41.59 1 0 .59 0 1-.59 1H.59C0 13 0 12.59 0 12c0-.59 0-1 .59-1z"/></svg>
    </button>

    <div class="site-header-menu">
      <nav class="site-header-nav">
        <a href="/features" class="js-selected-navigation-item nav-item" data-ga-click="Header, click, Nav menu - item:features" data-selected-links="/features /features">
          Features
</a>        <a href="/business" class="js-selected-navigation-item nav-item" data-ga-click="Header, click, Nav menu - item:business" data-selected-links="/business /business/security /business/customers /business">
          Business
</a>        <a href="/explore" class="js-selected-navigation-item nav-item" data-ga-click="Header, click, Nav menu - item:explore" data-selected-links="/explore /trending /trending/developers /integrations /integrations/feature/code /integrations/feature/collaborate /integrations/feature/ship /showcases /explore">
          Explore
</a>        <a href="/pricing" class="js-selected-navigation-item nav-item" data-ga-click="Header, click, Nav menu - item:pricing" data-selected-links="/pricing /pricing/developer /pricing/team /pricing/business-hosted /pricing/business-enterprise /pricing">
          Pricing
</a>      </nav>

      <div class="site-header-actions">
          <div class="header-search scoped-search site-scoped-search js-site-search" role="search">
  <!-- '"` --><!-- </textarea></xmp> --></option></form><form accept-charset="UTF-8" action="/CivicKnowledge/metatab-py/search" class="js-site-search-form" data-scoped-search-url="/CivicKnowledge/metatab-py/search" data-unscoped-search-url="/search" method="get"><div style="margin:0;padding:0;display:inline"><input name="utf8" type="hidden" value="&#x2713;" /></div>
    <label class="form-control header-search-wrapper js-chromeless-input-container">
        <a href="/CivicKnowledge/metatab-py/blob/master/README.rst" class="header-search-scope no-underline">This repository</a>
      <input type="text"
        class="form-control header-search-input js-site-search-focus js-site-search-field is-clearable"
        data-hotkey="s"
        name="q"
        value=""
        placeholder="Search"
        aria-label="Search this repository"
        data-unscoped-placeholder="Search GitHub"
        data-scoped-placeholder="Search"
        autocapitalize="off">
        <input type="hidden" class="js-site-search-type-field" name="type" >
    </label>
</form></div>


          <a class="text-bold site-header-link" href="/login?return_to=%2FCivicKnowledge%2Fmetatab-py%2Fblob%2Fmaster%2FREADME.rst" data-ga-click="(Logged out) Header, clicked Sign in, text:sign-in">Sign in</a>
            <span class="text-gray">or</span>
            <a class="text-bold site-header-link" href="/join?source=header-repo" data-ga-click="(Logged out) Header, clicked Sign up, text:sign-up">Sign up</a>
      </div>
    </div>
  </div>
</header>


  </div>

  <div id="start-of-content" class="accessibility-aid"></div>

    <div id="js-flash-container">
</div>



  <div role="main">
        <div itemscope itemtype="http://schema.org/SoftwareSourceCode">
    <div id="js-repo-pjax-container" data-pjax-container>
        



  <div class="pagehead repohead instapaper_ignore readability-menu experiment-repo-nav">
    <div class="container repohead-details-container">


      <ul class="pagehead-actions">
  <li>
      <a href="/login?return_to=%2FCivicKnowledge%2Fmetatab-py"
    class="btn btn-sm btn-with-count tooltipped tooltipped-n"
    aria-label="You must be signed in to watch a repository" rel="nofollow">
    <svg aria-hidden="true" class="octicon octicon-eye" height="16" version="1.1" viewBox="0 0 16 16" width="16"><path fill-rule="evenodd" d="M8.06 2C3 2 0 8 0 8s3 6 8.06 6C13 14 16 8 16 8s-3-6-7.94-6zM8 12c-2.2 0-4-1.78-4-4 0-2.2 1.8-4 4-4 2.22 0 4 1.8 4 4 0 2.22-1.78 4-4 4zm2-4c0 1.11-.89 2-2 2-1.11 0-2-.89-2-2 0-1.11.89-2 2-2 1.11 0 2 .89 2 2z"/></svg>
    Watch
  </a>
  <a class="social-count" href="/CivicKnowledge/metatab-py/watchers"
     aria-label="2 users are watching this repository">
    2
  </a>

  </li>

  <li>
      <a href="/login?return_to=%2FCivicKnowledge%2Fmetatab-py"
    class="btn btn-sm btn-with-count tooltipped tooltipped-n"
    aria-label="You must be signed in to star a repository" rel="nofollow">
    <svg aria-hidden="true" class="octicon octicon-star" height="16" version="1.1" viewBox="0 0 14 16" width="14"><path fill-rule="evenodd" d="M14 6l-4.9-.64L7 1 4.9 5.36 0 6l3.6 3.26L2.67 14 7 11.67 11.33 14l-.93-4.74z"/></svg>
    Star
  </a>

    <a class="social-count js-social-count" href="/CivicKnowledge/metatab-py/stargazers"
      aria-label="4 users starred this repository">
      4
    </a>

  </li>

  <li>
      <a href="/login?return_to=%2FCivicKnowledge%2Fmetatab-py"
        class="btn btn-sm btn-with-count tooltipped tooltipped-n"
        aria-label="You must be signed in to fork a repository" rel="nofollow">
        <svg aria-hidden="true" class="octicon octicon-repo-forked" height="16" version="1.1" viewBox="0 0 10 16" width="10"><path fill-rule="evenodd" d="M8 1a1.993 1.993 0 0 0-1 3.72V6L5 8 3 6V4.72A1.993 1.993 0 0 0 2 1a1.993 1.993 0 0 0-1 3.72V6.5l3 3v1.78A1.993 1.993 0 0 0 5 15a1.993 1.993 0 0 0 1-3.72V9.5l3-3V4.72A1.993 1.993 0 0 0 8 1zM2 4.2C1.34 4.2.8 3.65.8 3c0-.65.55-1.2 1.2-1.2.65 0 1.2.55 1.2 1.2 0 .65-.55 1.2-1.2 1.2zm3 10c-.66 0-1.2-.55-1.2-1.2 0-.65.55-1.2 1.2-1.2.65 0 1.2.55 1.2 1.2 0 .65-.55 1.2-1.2 1.2zm3-10c-.66 0-1.2-.55-1.2-1.2 0-.65.55-1.2 1.2-1.2.65 0 1.2.55 1.2 1.2 0 .65-.55 1.2-1.2 1.2z"/></svg>
        Fork
      </a>

    <a href="/CivicKnowledge/metatab-py/network" class="social-count"
       aria-label="1 user forked this repository">
      1
    </a>
  </li>
</ul>

      <h1 class="public ">
  <svg aria-hidden="true" class="octicon octicon-repo" height="16" version="1.1" viewBox="0 0 12 16" width="12"><path fill-rule="evenodd" d="M4 9H3V8h1v1zm0-3H3v1h1V6zm0-2H3v1h1V4zm0-2H3v1h1V2zm8-1v12c0 .55-.45 1-1 1H6v2l-1.5-1.5L3 16v-2H1c-.55 0-1-.45-1-1V1c0-.55.45-1 1-1h10c.55 0 1 .45 1 1zm-1 10H1v2h2v-1h3v1h5v-2zm0-10H2v9h9V1z"/></svg>
  <span class="author" itemprop="author"><a href="/CivicKnowledge" class="url fn" rel="author">CivicKnowledge</a></span><!--
--><span class="path-divider">/</span><!--
--><strong itemprop="name"><a href="/CivicKnowledge/metatab-py" data-pjax="#js-repo-pjax-container">metatab-py</a></strong>

</h1>

    </div>
    <div class="container">
      
<nav class="reponav js-repo-nav js-sidenav-container-pjax"
     itemscope
     itemtype="http://schema.org/BreadcrumbList"
     role="navigation"
     data-pjax="#js-repo-pjax-container">

  <span itemscope itemtype="http://schema.org/ListItem" itemprop="itemListElement">
    <a href="/CivicKnowledge/metatab-py" class="js-selected-navigation-item selected reponav-item" data-hotkey="g c" data-selected-links="repo_source repo_downloads repo_commits repo_releases repo_tags repo_branches /CivicKnowledge/metatab-py" itemprop="url">
      <svg aria-hidden="true" class="octicon octicon-code" height="16" version="1.1" viewBox="0 0 14 16" width="14"><path fill-rule="evenodd" d="M9.5 3L8 4.5 11.5 8 8 11.5 9.5 13 14 8 9.5 3zm-5 0L0 8l4.5 5L6 11.5 2.5 8 6 4.5 4.5 3z"/></svg>
      <span itemprop="name">Code</span>
      <meta itemprop="position" content="1">
</a>  </span>

    <span itemscope itemtype="http://schema.org/ListItem" itemprop="itemListElement">
      <a href="/CivicKnowledge/metatab-py/issues" class="js-selected-navigation-item reponav-item" data-hotkey="g i" data-selected-links="repo_issues repo_labels repo_milestones /CivicKnowledge/metatab-py/issues" itemprop="url">
        <svg aria-hidden="true" class="octicon octicon-issue-opened" height="16" version="1.1" viewBox="0 0 14 16" width="14"><path fill-rule="evenodd" d="M7 2.3c3.14 0 5.7 2.56 5.7 5.7s-2.56 5.7-5.7 5.7A5.71 5.71 0 0 1 1.3 8c0-3.14 2.56-5.7 5.7-5.7zM7 1C3.14 1 0 4.14 0 8s3.14 7 7 7 7-3.14 7-7-3.14-7-7-7zm1 3H6v5h2V4zm0 6H6v2h2v-2z"/></svg>
        <span itemprop="name">Issues</span>
        <span class="Counter">5</span>
        <meta itemprop="position" content="2">
</a>    </span>

  <span itemscope itemtype="http://schema.org/ListItem" itemprop="itemListElement">
    <a href="/CivicKnowledge/metatab-py/pulls" class="js-selected-navigation-item reponav-item" data-hotkey="g p" data-selected-links="repo_pulls /CivicKnowledge/metatab-py/pulls" itemprop="url">
      <svg aria-hidden="true" class="octicon octicon-git-pull-request" height="16" version="1.1" viewBox="0 0 12 16" width="12"><path fill-rule="evenodd" d="M11 11.28V5c-.03-.78-.34-1.47-.94-2.06C9.46 2.35 8.78 2.03 8 2H7V0L4 3l3 3V4h1c.27.02.48.11.69.31.21.2.3.42.31.69v6.28A1.993 1.993 0 0 0 10 15a1.993 1.993 0 0 0 1-3.72zm-1 2.92c-.66 0-1.2-.55-1.2-1.2 0-.65.55-1.2 1.2-1.2.65 0 1.2.55 1.2 1.2 0 .65-.55 1.2-1.2 1.2zM4 3c0-1.11-.89-2-2-2a1.993 1.993 0 0 0-1 3.72v6.56A1.993 1.993 0 0 0 2 15a1.993 1.993 0 0 0 1-3.72V4.72c.59-.34 1-.98 1-1.72zm-.8 10c0 .66-.55 1.2-1.2 1.2-.65 0-1.2-.55-1.2-1.2 0-.65.55-1.2 1.2-1.2.65 0 1.2.55 1.2 1.2zM2 4.2C1.34 4.2.8 3.65.8 3c0-.65.55-1.2 1.2-1.2.65 0 1.2.55 1.2 1.2 0 .65-.55 1.2-1.2 1.2z"/></svg>
      <span itemprop="name">Pull requests</span>
      <span class="Counter">0</span>
      <meta itemprop="position" content="3">
</a>  </span>

    <a href="/CivicKnowledge/metatab-py/projects" class="js-selected-navigation-item reponav-item" data-selected-links="repo_projects new_repo_project repo_project /CivicKnowledge/metatab-py/projects">
      <svg aria-hidden="true" class="octicon octicon-project" height="16" version="1.1" viewBox="0 0 15 16" width="15"><path fill-rule="evenodd" d="M10 12h3V2h-3v10zm-4-2h3V2H6v8zm-4 4h3V2H2v12zm-1 1h13V1H1v14zM14 0H1a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h13a1 1 0 0 0 1-1V1a1 1 0 0 0-1-1z"/></svg>
      Projects
      <span class="Counter" >0</span>
</a>


  <a href="/CivicKnowledge/metatab-py/pulse" class="js-selected-navigation-item reponav-item" data-selected-links="pulse /CivicKnowledge/metatab-py/pulse">
    <svg aria-hidden="true" class="octicon octicon-pulse" height="16" version="1.1" viewBox="0 0 14 16" width="14"><path fill-rule="evenodd" d="M11.5 8L8.8 5.4 6.6 8.5 5.5 1.6 2.38 8H0v2h3.6l.9-1.8.9 5.4L9 8.5l1.6 1.5H14V8z"/></svg>
    Pulse
</a>
  <a href="/CivicKnowledge/metatab-py/graphs" class="js-selected-navigation-item reponav-item" data-selected-links="repo_graphs repo_contributors /CivicKnowledge/metatab-py/graphs">
    <svg aria-hidden="true" class="octicon octicon-graph" height="16" version="1.1" viewBox="0 0 16 16" width="16"><path fill-rule="evenodd" d="M16 14v1H0V0h1v14h15zM5 13H3V8h2v5zm4 0H7V3h2v10zm4 0h-2V6h2v7z"/></svg>
    Graphs
</a>

</nav>

    </div>
  </div>

<div class="container new-discussion-timeline experiment-repo-nav">
  <div class="repository-content">

    
          

<a href="/CivicKnowledge/metatab-py/blob/840b808cbf96222c63210cb8a2d0821ec834a8d7/README.rst" class="d-none js-permalink-shortcut" data-hotkey="y">Permalink</a>

<!-- blob contrib key: blob_contributors:v21:6765545888d6537585aa099284e4cf6d -->

<div class="file-navigation js-zeroclipboard-container">
  
<div class="select-menu branch-select-menu js-menu-container js-select-menu float-left">
  <button class=" btn btn-sm select-menu-button js-menu-target css-truncate" data-hotkey="w"
    
    type="button" aria-label="Switch branches or tags" tabindex="0" aria-haspopup="true">
      <i>Branch:</i>
      <span class="js-select-button css-truncate-target">master</span>
  </button>

  <div class="select-menu-modal-holder js-menu-content js-navigation-container" data-pjax>

    <div class="select-menu-modal">
      <div class="select-menu-header">
        <svg aria-label="Close" class="octicon octicon-x js-menu-close" height="16" role="img" version="1.1" viewBox="0 0 12 16" width="12"><path fill-rule="evenodd" d="M7.48 8l3.75 3.75-1.48 1.48L6 9.48l-3.75 3.75-1.48-1.48L4.52 8 .77 4.25l1.48-1.48L6 6.52l3.75-3.75 1.48 1.48z"/></svg>
        <span class="select-menu-title">Switch branches/tags</span>
      </div>

      <div class="select-menu-filters">
        <div class="select-menu-text-filter">
          <input type="text" aria-label="Filter branches/tags" id="context-commitish-filter-field" class="form-control js-filterable-field js-navigation-enable" placeholder="Filter branches/tags">
        </div>
        <div class="select-menu-tabs">
          <ul>
            <li class="select-menu-tab">
              <a href="#" data-tab-filter="branches" data-filter-placeholder="Filter branches/tags" class="js-select-menu-tab" role="tab">Branches</a>
            </li>
            <li class="select-menu-tab">
              <a href="#" data-tab-filter="tags" data-filter-placeholder="Find a tag…" class="js-select-menu-tab" role="tab">Tags</a>
            </li>
          </ul>
        </div>
      </div>

      <div class="select-menu-list select-menu-tab-bucket js-select-menu-tab-bucket" data-tab-filter="branches" role="menu">

        <div data-filterable-for="context-commitish-filter-field" data-filterable-type="substring">


            <a class="select-menu-item js-navigation-item js-navigation-open "
               href="/CivicKnowledge/metatab-py/blob/issue%232/README.rst"
               data-name="issue#2"
               data-skip-pjax="true"
               rel="nofollow">
              <svg aria-hidden="true" class="octicon octicon-check select-menu-item-icon" height="16" version="1.1" viewBox="0 0 12 16" width="12"><path fill-rule="evenodd" d="M12 5l-8 8-4-4 1.5-1.5L4 10l6.5-6.5z"/></svg>
              <span class="select-menu-item-text css-truncate-target js-select-menu-filter-text">
                issue#2
              </span>
            </a>
            <a class="select-menu-item js-navigation-item js-navigation-open selected"
               href="/CivicKnowledge/metatab-py/blob/master/README.rst"
               data-name="master"
               data-skip-pjax="true"
               rel="nofollow">
              <svg aria-hidden="true" class="octicon octicon-check select-menu-item-icon" height="16" version="1.1" viewBox="0 0 12 16" width="12"><path fill-rule="evenodd" d="M12 5l-8 8-4-4 1.5-1.5L4 10l6.5-6.5z"/></svg>
              <span class="select-menu-item-text css-truncate-target js-select-menu-filter-text">
                master
              </span>
            </a>
        </div>

          <div class="select-menu-no-results">Nothing to show</div>
      </div>

      <div class="select-menu-list select-menu-tab-bucket js-select-menu-tab-bucket" data-tab-filter="tags">
        <div data-filterable-for="context-commitish-filter-field" data-filterable-type="substring">


            <a class="select-menu-item js-navigation-item js-navigation-open "
              href="/CivicKnowledge/metatab-py/tree/v0.3.7/README.rst"
              data-name="v0.3.7"
              data-skip-pjax="true"
              rel="nofollow">
              <svg aria-hidden="true" class="octicon octicon-check select-menu-item-icon" height="16" version="1.1" viewBox="0 0 12 16" width="12"><path fill-rule="evenodd" d="M12 5l-8 8-4-4 1.5-1.5L4 10l6.5-6.5z"/></svg>
              <span class="select-menu-item-text css-truncate-target" title="v0.3.7">
                v0.3.7
              </span>
            </a>
            <a class="select-menu-item js-navigation-item js-navigation-open "
              href="/CivicKnowledge/metatab-py/tree/v0.3.6/README.rst"
              data-name="v0.3.6"
              data-skip-pjax="true"
              rel="nofollow">
              <svg aria-hidden="true" class="octicon octicon-check select-menu-item-icon" height="16" version="1.1" viewBox="0 0 12 16" width="12"><path fill-rule="evenodd" d="M12 5l-8 8-4-4 1.5-1.5L4 10l6.5-6.5z"/></svg>
              <span class="select-menu-item-text css-truncate-target" title="v0.3.6">
                v0.3.6
              </span>
            </a>
            <a class="select-menu-item js-navigation-item js-navigation-open "
              href="/CivicKnowledge/metatab-py/tree/v0.3.5/README.rst"
              data-name="v0.3.5"
              data-skip-pjax="true"
              rel="nofollow">
              <svg aria-hidden="true" class="octicon octicon-check select-menu-item-icon" height="16" version="1.1" viewBox="0 0 12 16" width="12"><path fill-rule="evenodd" d="M12 5l-8 8-4-4 1.5-1.5L4 10l6.5-6.5z"/></svg>
              <span class="select-menu-item-text css-truncate-target" title="v0.3.5">
                v0.3.5
              </span>
            </a>
            <a class="select-menu-item js-navigation-item js-navigation-open "
              href="/CivicKnowledge/metatab-py/tree/v0.3.4/README.rst"
              data-name="v0.3.4"
              data-skip-pjax="true"
              rel="nofollow">
              <svg aria-hidden="true" class="octicon octicon-check select-menu-item-icon" height="16" version="1.1" viewBox="0 0 12 16" width="12"><path fill-rule="evenodd" d="M12 5l-8 8-4-4 1.5-1.5L4 10l6.5-6.5z"/></svg>
              <span class="select-menu-item-text css-truncate-target" title="v0.3.4">
                v0.3.4
              </span>
            </a>
            <a class="select-menu-item js-navigation-item js-navigation-open "
              href="/CivicKnowledge/metatab-py/tree/v0.3.2/README.rst"
              data-name="v0.3.2"
              data-skip-pjax="true"
              rel="nofollow">
              <svg aria-hidden="true" class="octicon octicon-check select-menu-item-icon" height="16" version="1.1" viewBox="0 0 12 16" width="12"><path fill-rule="evenodd" d="M12 5l-8 8-4-4 1.5-1.5L4 10l6.5-6.5z"/></svg>
              <span class="select-menu-item-text css-truncate-target" title="v0.3.2">
                v0.3.2
              </span>
            </a>
            <a class="select-menu-item js-navigation-item js-navigation-open "
              href="/CivicKnowledge/metatab-py/tree/v0.3.1/README.rst"
              data-name="v0.3.1"
              data-skip-pjax="true"
              rel="nofollow">
              <svg aria-hidden="true" class="octicon octicon-check select-menu-item-icon" height="16" version="1.1" viewBox="0 0 12 16" width="12"><path fill-rule="evenodd" d="M12 5l-8 8-4-4 1.5-1.5L4 10l6.5-6.5z"/></svg>
              <span class="select-menu-item-text css-truncate-target" title="v0.3.1">
                v0.3.1
              </span>
            </a>
            <a class="select-menu-item js-navigation-item js-navigation-open "
              href="/CivicKnowledge/metatab-py/tree/0.2.9.c/README.rst"
              data-name="0.2.9.c"
              data-skip-pjax="true"
              rel="nofollow">
              <svg aria-hidden="true" class="octicon octicon-check select-menu-item-icon" height="16" version="1.1" viewBox="0 0 12 16" width="12"><path fill-rule="evenodd" d="M12 5l-8 8-4-4 1.5-1.5L4 10l6.5-6.5z"/></svg>
              <span class="select-menu-item-text css-truncate-target" title="0.2.9.c">
                0.2.9.c
              </span>
            </a>
            <a class="select-menu-item js-navigation-item js-navigation-open "
              href="/CivicKnowledge/metatab-py/tree/0.2.8/README.rst"
              data-name="0.2.8"
              data-skip-pjax="true"
              rel="nofollow">
              <svg aria-hidden="true" class="octicon octicon-check select-menu-item-icon" height="16" version="1.1" viewBox="0 0 12 16" width="12"><path fill-rule="evenodd" d="M12 5l-8 8-4-4 1.5-1.5L4 10l6.5-6.5z"/></svg>
              <span class="select-menu-item-text css-truncate-target" title="0.2.8">
                0.2.8
              </span>
            </a>
            <a class="select-menu-item js-navigation-item js-navigation-open "
              href="/CivicKnowledge/metatab-py/tree/0.2.6/README.rst"
              data-name="0.2.6"
              data-skip-pjax="true"
              rel="nofollow">
              <svg aria-hidden="true" class="octicon octicon-check select-menu-item-icon" height="16" version="1.1" viewBox="0 0 12 16" width="12"><path fill-rule="evenodd" d="M12 5l-8 8-4-4 1.5-1.5L4 10l6.5-6.5z"/></svg>
              <span class="select-menu-item-text css-truncate-target" title="0.2.6">
                0.2.6
              </span>
            </a>
        </div>

        <div class="select-menu-no-results">Nothing to show</div>
      </div>

    </div>
  </div>
</div>

  <div class="BtnGroup float-right">
    <a href="/CivicKnowledge/metatab-py/find/master"
          class="js-pjax-capture-input btn btn-sm BtnGroup-item"
          data-pjax
          data-hotkey="t">
      Find file
    </a>
    <button aria-label="Copy file path to clipboard" class="js-zeroclipboard btn btn-sm BtnGroup-item tooltipped tooltipped-s" data-copied-hint="Copied!" type="button">Copy path</button>
  </div>
  <div class="breadcrumb js-zeroclipboard-target">
    <span class="repo-root js-repo-root"><span class="js-path-segment"><a href="/CivicKnowledge/metatab-py"><span>metatab-py</span></a></span></span><span class="separator">/</span><strong class="final-path">README.rst</strong>
  </div>
</div>


<include-fragment class="commit-tease" src="/CivicKnowledge/metatab-py/contributors/master/README.rst">
  <div>
    Fetching contributors&hellip;
  </div>

  <div class="commit-tease-contributors">
    <img alt="" class="loader-loading float-left" height="16" src="https://assets-cdn.github.com/images/spinners/octocat-spinner-32-EAF2F5.gif" width="16" />
    <span class="loader-error">Cannot retrieve contributors at this time</span>
  </div>
</include-fragment>
<div class="file">
  <div class="file-header">
  <div class="file-actions">

    <div class="BtnGroup">
      <a href="/CivicKnowledge/metatab-py/raw/master/README.rst" class="btn btn-sm BtnGroup-item" id="raw-url">Raw</a>
        <a href="/CivicKnowledge/metatab-py/blame/master/README.rst" class="btn btn-sm js-update-url-with-hash BtnGroup-item" data-hotkey="b">Blame</a>
      <a href="/CivicKnowledge/metatab-py/commits/master/README.rst" class="btn btn-sm BtnGroup-item" rel="nofollow">History</a>
    </div>


        <button type="button" class="btn-octicon disabled tooltipped tooltipped-nw"
          aria-label="You must be signed in to make or propose changes">
          <svg aria-hidden="true" class="octicon octicon-pencil" height="16" version="1.1" viewBox="0 0 14 16" width="14"><path fill-rule="evenodd" d="M0 12v3h3l8-8-3-3-8 8zm3 2H1v-2h1v1h1v1zm10.3-9.3L12 6 9 3l1.3-1.3a.996.996 0 0 1 1.41 0l1.59 1.59c.39.39.39 1.02 0 1.41z"/></svg>
        </button>
        <button type="button" class="btn-octicon btn-octicon-danger disabled tooltipped tooltipped-nw"
          aria-label="You must be signed in to make or propose changes">
          <svg aria-hidden="true" class="octicon octicon-trashcan" height="16" version="1.1" viewBox="0 0 12 16" width="12"><path fill-rule="evenodd" d="M11 2H9c0-.55-.45-1-1-1H5c-.55 0-1 .45-1 1H2c-.55 0-1 .45-1 1v1c0 .55.45 1 1 1v9c0 .55.45 1 1 1h7c.55 0 1-.45 1-1V5c.55 0 1-.45 1-1V3c0-.55-.45-1-1-1zm-1 12H3V5h1v8h1V5h1v8h1V5h1v8h1V5h1v9zm1-10H2V3h9v1z"/></svg>
        </button>
  </div>

  <div class="file-info">
      335 lines (185 sloc)
      <span class="file-info-divider"></span>
    19.4 KB
  </div>
</div>

  
  <div id="readme" class="readme blob instapaper_body">
    <article class="markdown-body entry-content" itemprop="text"><h1><a id="user-content-metatab" class="anchor" href="#metatab" aria-hidden="true"><svg aria-hidden="true" class="octicon octicon-link" height="16" version="1.1" viewBox="0 0 16 16" width="16"><path fill-rule="evenodd" d="M4 9h1v1H4c-1.5 0-3-1.69-3-3.5S2.55 3 4 3h4c1.45 0 3 1.69 3 3.5 0 1.41-.91 2.72-2 3.25V8.59c.58-.45 1-1.27 1-2.09C10 5.22 8.98 4 8 4H4c-.98 0-2 1.22-2 2.5S3 9 4 9zm9-3h-1v1h1c1 0 2 1.22 2 2.5S13.98 12 13 12H9c-.98 0-2-1.22-2-2.5 0-.83.42-1.64 1-2.09V6.25c-1.09.53-2 1.84-2 3.25C6 11.31 7.55 13 9 13h4c1.45 0 3-1.69 3-3.5S14.5 6 13 6z"></path></svg></a>Metatab</h1>
<p>Parse and manipulate structured data and metadata in a tabular format.</p>
<p><a href="http://metatab.org">Metatab</a> is a data format that allows structured metadata -- the sort you'd normally store in JSON, YAML or XML -- to be stored and edited in tabular forms like CSV or Excel. Metatab files look exactly like you'd expect, so they
are very easy for non-technical users to read and edit, using tools they already have. Metatab is an excellent format
for creating, storing and transmitting metadata. For more information about metatab, visit <a href="http://metatab.org">http://metatab.org</a>.</p>
<p>This repository has a Python module and executable. For a Javascript version, see the <a href="https://github.com/CivicKnowledge/metatab-js">metatab-js</a> repository.</p>
<a name="user-content-what-is-metatab-for"></a>
<h2><a id="user-content-what-is-metatab-for" class="anchor" href="#what-is-metatab-for" aria-hidden="true"><svg aria-hidden="true" class="octicon octicon-link" height="16" version="1.1" viewBox="0 0 16 16" width="16"><path fill-rule="evenodd" d="M4 9h1v1H4c-1.5 0-3-1.69-3-3.5S2.55 3 4 3h4c1.45 0 3 1.69 3 3.5 0 1.41-.91 2.72-2 3.25V8.59c.58-.45 1-1.27 1-2.09C10 5.22 8.98 4 8 4H4c-.98 0-2 1.22-2 2.5S3 9 4 9zm9-3h-1v1h1c1 0 2 1.22 2 2.5S13.98 12 13 12H9c-.98 0-2-1.22-2-2.5 0-.83.42-1.64 1-2.09V6.25c-1.09.53-2 1.84-2 3.25C6 11.31 7.55 13 9 13h4c1.45 0 3-1.69 3-3.5S14.5 6 13 6z"></path></svg></a>What is Metatab For?</h2>
<p>Metatab is a tabular format that allows storing metadata for demographics, health and research datasets in a tabular format. The tabular format is much easier for data creators to write and for data consumers to read, and it allows a complete data packages to be stored in a single Excel file.</p>
<a name="user-content-install"></a>
<h2><a id="user-content-install" class="anchor" href="#install" aria-hidden="true"><svg aria-hidden="true" class="octicon octicon-link" height="16" version="1.1" viewBox="0 0 16 16" width="16"><path fill-rule="evenodd" d="M4 9h1v1H4c-1.5 0-3-1.69-3-3.5S2.55 3 4 3h4c1.45 0 3 1.69 3 3.5 0 1.41-.91 2.72-2 3.25V8.59c.58-.45 1-1.27 1-2.09C10 5.22 8.98 4 8 4H4c-.98 0-2 1.22-2 2.5S3 9 4 9zm9-3h-1v1h1c1 0 2 1.22 2 2.5S13.98 12 13 12H9c-.98 0-2-1.22-2-2.5 0-.83.42-1.64 1-2.09V6.25c-1.09.53-2 1.84-2 3.25C6 11.31 7.55 13 9 13h4c1.45 0 3-1.69 3-3.5S14.5 6 13 6z"></path></svg></a>Install</h2>
<p>Install the package from PiPy with:</p>
<div class="highlight highlight-source-shell"><pre>$ pip install metatab</pre></div>
<p>Or, install the master branch from github with:</p>
<div class="highlight highlight-source-shell"><pre>$ pip install https://github.com/CivicKnowledge/metatab-py.git</pre></div>
<p>Then test parsing using a remote file with:</p>
<div class="highlight highlight-source-shell"><pre>$ metatab -j https://raw.githubusercontent.com/CivicKnowledge/metatab-py/master/test-data/example1.csv</pre></div>
<p>Run <code>metatab -h</code> to get other program options.</p>
<p>The <code>test-data</code> directory has test files that also serve as examples to parse. You can either clone the repo and parse them from the files, or from the Github page for the file, click on the <code>raw</code> button to get raw view of the flie, then copy the URL.</p>
<a name="user-content-metatab-and-metapack"></a>
<h2><a id="user-content-metatab-and-metapack" class="anchor" href="#metatab-and-metapack" aria-hidden="true"><svg aria-hidden="true" class="octicon octicon-link" height="16" version="1.1" viewBox="0 0 16 16" width="16"><path fill-rule="evenodd" d="M4 9h1v1H4c-1.5 0-3-1.69-3-3.5S2.55 3 4 3h4c1.45 0 3 1.69 3 3.5 0 1.41-.91 2.72-2 3.25V8.59c.58-.45 1-1.27 1-2.09C10 5.22 8.98 4 8 4H4c-.98 0-2 1.22-2 2.5S3 9 4 9zm9-3h-1v1h1c1 0 2 1.22 2 2.5S13.98 12 13 12H9c-.98 0-2-1.22-2-2.5 0-.83.42-1.64 1-2.09V6.25c-1.09.53-2 1.84-2 3.25C6 11.31 7.55 13 9 13h4c1.45 0 3-1.69 3-3.5S14.5 6 13 6z"></path></svg></a>Metatab and Metapack</h2>
<p>The metatab Python distribution includes two programs, <code>metatab</code> for manipulating single Metatab files  and <code>metapack</code> for creating data packages. The two programs share some options, so when building packages, you can use the <code>metapack</code> program exclusively, and <code>metatab</code> is most useful for converting Metatab files to JSON. This tutorial will primarily use <code>metapack</code></p>
<a name="user-content-creating-a-new-package"></a>
<h2><a id="user-content-creating-a-new-package" class="anchor" href="#creating-a-new-package" aria-hidden="true"><svg aria-hidden="true" class="octicon octicon-link" height="16" version="1.1" viewBox="0 0 16 16" width="16"><path fill-rule="evenodd" d="M4 9h1v1H4c-1.5 0-3-1.69-3-3.5S2.55 3 4 3h4c1.45 0 3 1.69 3 3.5 0 1.41-.91 2.72-2 3.25V8.59c.58-.45 1-1.27 1-2.09C10 5.22 8.98 4 8 4H4c-.98 0-2 1.22-2 2.5S3 9 4 9zm9-3h-1v1h1c1 0 2 1.22 2 2.5S13.98 12 13 12H9c-.98 0-2-1.22-2-2.5 0-.83.42-1.64 1-2.09V6.25c-1.09.53-2 1.84-2 3.25C6 11.31 7.55 13 9 13h4c1.45 0 3-1.69 3-3.5S14.5 6 13 6z"></path></svg></a>Creating a new package</h2>
<p>[ For an overview of the Metatab format, see the <a href="http://www.metatab.org/">Metatab specifications</a>. ]</p>
<p>Create a directory, usually with the name you'll give the package and create a new metatab file within it.</p>
<div class="highlight highlight-source-shell"><pre>$ mkdir example-data-package
$ <span class="pl-c1">cd</span> example-data-package
$ metapack -c</pre></div>
<p>The <code>metapack -c</code> command will create a new Metatab file in the current directory, <code>metadata.csv</code>. You can open this file with a spreadsheet program to edit it.</p>
<p>Tne only required term to set is <code>Name</code>, but you should have values for <code>Title</code> and <code>Description.</code> Initially, the <code>Name</code> is set to the same values as <code>Identity</code>, which is set to a randuom UUID4.</p>
<p>For this example, the <code>Name</code> term could be changed to the name of the directory, 'example-package.' However, it is more rigorous to set the name component terms, <code>DatasetName</code> and zero or more of <code>Origin</code>, <code>Version</code>, <code>Time</code> or <code>Space</code>. These terms will be combined to make the name, and the name will include important components to distinguish different package versions and similar datasets from different sources. The <code>Name</code> term is used to generate files names when making ZIP, Excel and S3 packages. For this tutorial use these values:</p>
<ul>
<li>DatasetName: 'example-data-package'</li>
<li>Origin ( in the 'Contacts' Section): 'example.com'</li>
<li>Version ( Automatically set ) : '1'</li>
<li>Space: 'US'</li>
<li>Time: '2017'</li>
</ul>
<blockquote>
These values will generate the name 'example.com-example_data_package-2017-us-1'. If you update the package, change the <code>Version</code> value and run <code>metapack -u</code> to regenerate the <code>Name</code>.</blockquote>
<p>After setting the <code>DatasetName</code>, <code>Origin</code>, <code>Version</code>, <code>Time</code> or <code>Space</code> and saving the file, , run <code>metapack -u</code> to update <code>Name</code>:</p>
<div class="highlight highlight-source-shell"><pre>$ metapack -u
Updated Root.Name to: <span class="pl-s"><span class="pl-pds">'</span>example.com-example_data_package-2017-us-1<span class="pl-pds">'</span></span></pre></div>
<p>Since this is a data package, it is important to have references to data. The package we are creating here is a filesystem package, and will usually reference the URLs to data on the web. Later, we will generate other packages, such as ZIP or Excel files, and the data will be downloaded and included directly in the package. We define the paths or URLs to data files with the <code>DataFile</code> term.</p>
<p>For the <code>Datafile</code> term, you can add entries directly, but it is easier to use the <code>metapack</code> program to add them. The <code>metapack -a</code> program will inspect the file for you, finding internal files in ZIP files and creating the correct URLs for Excel files.</p>
<p>If you have made changes to the <code>metadata.csv</code> file, save it, then run:</p>
<div class="highlight highlight-source-shell"><pre>$ metapack -a http://public.source.civicknowledge.com/example.com/sources/test_data.zip</pre></div>
<p>The <code>test_data.zip</code> file is a test file with many types of tabular datafiles within it. The <code>metapack -a</code> command will download it, open it, find all of the data files int it, and add URLs to the metatab. If any of the files in the zip file are Excel format, it will also create URLs for each of the tabs.</p>
<p>( This file is large and may take awhile. If you need a smaller file, try: <a href="http://public.source.civicknowledge.com/example.com/sources/renter_cost.csv">http://public.source.civicknowledge.com/example.com/sources/renter_cost.csv</a> )</p>
<p>The <code>metapack -a</code> command also works on directories and webpages. For instance, if you wanted to scrape all of the 60 data files for the California English Language Development Test, you could run:</p>
<div class="highlight highlight-source-shell"><pre>metapack -a http://celdt.cde.ca.gov/research/admin1516/indexcsv.asp</pre></div>
<p>Now reload the file. The Resource section should have 9 <code>Datafile</code> entries, all of them with fragments. The fragments will be URL encoded, so are a bit hard to read. %2F is a '/' and %3B is a ';'. The <code>metatab -a</code> program will also add a name, and try to get where the data starts and which lines are for headers.</p>
<p>Note that the <code>unicode-latin1</code> and <code>unicode-utf8</code> do not have values for StartLine and HeaderLines. This is because the row intuiting process failed to categorize the lines, because all of them are mostly strings. In these cases, download the file and examine it. For these two files, you can enter '0' for <code>HeaderLines</code> and '1' for <code>StartLine.</code></p>
<p>If you enter the <code>Datafile</code> terms manually, you should enter the URL for the datafile, ( in the cell below "Resources" ) and the <code>Name</code> value. If the URL to the resource is a zip file or an Excel file, you can use a URL fragment to indicate the inner filename. For Excel files, the fragment is either the name of the tab in the file, or the number of the tab. ( The first number is 0 ). If the resource is a zip file that holds an Excel file, the fragment can have both the internal file name and the tab number, separated by a semicolon ';' For instance:</p>
<ul>
<li><a href="http://public.source.civicknowledge.com/example.com/sources/test_data.zip#simple-example.csv">http://public.source.civicknowledge.com/example.com/sources/test_data.zip#simple-example.csv</a></li>
<li><a href="http://example.com/renter_cost_excel07.xlsx#2">http://example.com/renter_cost_excel07.xlsx#2</a></li>
<li><a href="http://example.com/test_data.zip#renter_cost_excel07.xlsx;B2">http://example.com/test_data.zip#renter_cost_excel07.xlsx;B2</a></li>
</ul>
<p>If you don't specify a tab name for an Excel file, the first will be used.</p>
<p>There are also URL forms for Google spreadsheet, S3 files and Socrata.</p>
<p>To test manually added URLs, use the <code>rowgen</code> program, which will download and cache the URL resource, then try to interpret it as a CSV or Excel file.</p>
<div class="highlight highlight-source-shell"><pre>$ rowgen http://public.source.civicknowledge.com/example.com/sources/test_data.zip#renter_cost_excel07.xlsx

------------------------  ------  ----------  ----------------  ----------------  -----------------
Renter Costs
This is a header comment

                                  renter                        owner
id                        gvid    cost_gt_30  cost_gt_30_cv     cost_gt_30_pct    cost_gt_30_pct_cv
1.0                       0O0P01  1447.0      13.6176070904818  42.2481751824818  8.27214070699712
2.0                       0O0P03  5581.0      6.23593207100335  49.280353200883   4.9333693053569
3.0                       0O0P05  525.0       17.6481586482953  45.2196382428941  13.2887199930555
4.0                       0O0P07  352.0       28.0619645779719  47.4393530997305  17.3833286873892</pre></div>
<p>( As of metatab 1.8, rowgenerator 0.0.7, some files with encodings that are not ascii or utf-8 will fail for Python2, but will work for Python3. )</p>
<p>Or just download the file and look at it. In this case, for both unicode-latin1 and unicode-utf8 you can see that the headers are on line 0 and the data starts on line 1 so enter those values into the metadata.csv file. Setting the <code>StartLine</code> and <code>HeaderLines</code> values is critical for properly generating schemas.</p>
<a name="user-content-generating-schemas"></a>
<h3><a id="user-content-generating-schemas" class="anchor" href="#generating-schemas" aria-hidden="true"><svg aria-hidden="true" class="octicon octicon-link" height="16" version="1.1" viewBox="0 0 16 16" width="16"><path fill-rule="evenodd" d="M4 9h1v1H4c-1.5 0-3-1.69-3-3.5S2.55 3 4 3h4c1.45 0 3 1.69 3 3.5 0 1.41-.91 2.72-2 3.25V8.59c.58-.45 1-1.27 1-2.09C10 5.22 8.98 4 8 4H4c-.98 0-2 1.22-2 2.5S3 9 4 9zm9-3h-1v1h1c1 0 2 1.22 2 2.5S13.98 12 13 12H9c-.98 0-2-1.22-2-2.5 0-.83.42-1.64 1-2.09V6.25c-1.09.53-2 1.84-2 3.25C6 11.31 7.55 13 9 13h4c1.45 0 3-1.69 3-3.5S14.5 6 13 6z"></path></svg></a>Generating Schemas</h3>
<p>Before generating schemas, be sure that the <code>StartLine</code> and <code>HeaderLines</code> properties are set for every <code>DataFile</code> term.</p>
<p>Now that the <code>metadata.csv</code> has resources specified, you can generate schemas for the resources with the metapack -s program.   First, save the file, then run:</p>
<div class="highlight highlight-source-shell"><pre>$ metapack -s</pre></div>
<p>Re-open  <code>metadata.csv</code> and you should see entries for tables and columns for each of the Datafiles. After creating the schema, you should edit the description ane possible change the alternate names (<code>AltName</code> terms. ) The alternate names are versions of the column headers that follow typical naming rules for columns. If an AltName is specified, iterating over the resource out of the package will use the AltName, rather than that column name.</p>
<a name="user-content-using-a-package"></a>
<h3><a id="user-content-using-a-package" class="anchor" href="#using-a-package" aria-hidden="true"><svg aria-hidden="true" class="octicon octicon-link" height="16" version="1.1" viewBox="0 0 16 16" width="16"><path fill-rule="evenodd" d="M4 9h1v1H4c-1.5 0-3-1.69-3-3.5S2.55 3 4 3h4c1.45 0 3 1.69 3 3.5 0 1.41-.91 2.72-2 3.25V8.59c.58-.45 1-1.27 1-2.09C10 5.22 8.98 4 8 4H4c-.98 0-2 1.22-2 2.5S3 9 4 9zm9-3h-1v1h1c1 0 2 1.22 2 2.5S13.98 12 13 12H9c-.98 0-2-1.22-2-2.5 0-.83.42-1.64 1-2.09V6.25c-1.09.53-2 1.84-2 3.25C6 11.31 7.55 13 9 13h4c1.45 0 3-1.69 3-3.5S14.5 6 13 6z"></path></svg></a>Using a Package</h3>
<p>At this point, the package is functionally complete, and you can check that the package is usable. First, list the resources with :</p>
<div class="highlight highlight-source-shell"><pre>$ metapack -R metadata.csv
random-names http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Fcsv%2Frandom-names.csv
renter_cost http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Fcsv%2Frenter_cost.csv
simple-example-altnames http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Fcsv%2Fsimple-example-altnames.csv
simple-example http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Fcsv%2Fsimple-example.csv
unicode-latin1 http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Fcsv%2Funicode-latin1.csv
unicode-utf8 http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Fcsv%2Funicode-utf8.csv
renter_cost_excel07 http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Fexcel%2Frenter_cost_excel07.xlsx%3BSheet1
renter_cost_excel97 http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Fexcel%2Frenter_cost_excel97.xls%3BSheet1
renter_cost-2 http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Ftab%2Frenter_cost.tsv</pre></div>
<p>You can dump one of the resources as a CSV by running the same command with the resource name as a fragment to the name of the metatab file:</p>
<div class="highlight highlight-source-shell"><pre>$ metapack -R metadata.csv#simple-example</pre></div>
<p>or:</p>
<div class="highlight highlight-source-shell"><pre>$ metapack -R <span class="pl-s"><span class="pl-pds">"</span>#simple-example<span class="pl-pds">"</span></span></pre></div>
<p>You can also read the resources from a Python program, with an easy way to convert a resource to a Pandas DataFrame.</p>
<div class="highlight highlight-source-python"><pre><span class="pl-k">import</span> metatab

doc <span class="pl-k">=</span> metatab.open_package(<span class="pl-s"><span class="pl-pds">'</span>.<span class="pl-pds">'</span></span>)  <span class="pl-c"><span class="pl-c">#</span> Will look for 'metadata.csv'</span>

<span class="pl-c1">print</span>(<span class="pl-c1">type</span>(doc))

<span class="pl-k">for</span> r <span class="pl-k">in</span> doc.resources():
    <span class="pl-c1">print</span>(r.name, r.url)

r <span class="pl-k">=</span> doc.first_resource(<span class="pl-s"><span class="pl-pds">'</span>renter_cost<span class="pl-pds">'</span></span>)

<span class="pl-c"><span class="pl-c">#</span> Dump the row</span>
<span class="pl-k">for</span> row <span class="pl-k">in</span> r:
    <span class="pl-c1">print</span> row


<span class="pl-c"><span class="pl-c">#</span> Or, turn it into a pandas dataframe</span>
<span class="pl-c"><span class="pl-c">#</span> ( After installing pandas )</span>

df <span class="pl-k">=</span> doc.first_resource(<span class="pl-s"><span class="pl-pds">'</span>renter_cost<span class="pl-pds">'</span></span>).dataframe()</pre></div>
<p>For a more complete example, see <a href="https://github.com/CivicKnowledge/metatab/blob/master/examples/Access%20Examples.ipynb">this Jupyter notebook example</a></p>
<a name="user-content-making-other-package-formats"></a>
<h3><a id="user-content-making-other-package-formats" class="anchor" href="#making-other-package-formats" aria-hidden="true"><svg aria-hidden="true" class="octicon octicon-link" height="16" version="1.1" viewBox="0 0 16 16" width="16"><path fill-rule="evenodd" d="M4 9h1v1H4c-1.5 0-3-1.69-3-3.5S2.55 3 4 3h4c1.45 0 3 1.69 3 3.5 0 1.41-.91 2.72-2 3.25V8.59c.58-.45 1-1.27 1-2.09C10 5.22 8.98 4 8 4H4c-.98 0-2 1.22-2 2.5S3 9 4 9zm9-3h-1v1h1c1 0 2 1.22 2 2.5S13.98 12 13 12H9c-.98 0-2-1.22-2-2.5 0-.83.42-1.64 1-2.09V6.25c-1.09.53-2 1.84-2 3.25C6 11.31 7.55 13 9 13h4c1.45 0 3-1.69 3-3.5S14.5 6 13 6z"></path></svg></a>Making Other Package Formats</h3>
<p>The tutorial above is actually creating a data package in a directory. There are several other forms of packages that Metapack can create including Excel, ZIP and S3.</p>
<div class="highlight highlight-source-shell"><pre>$ metapack -e <span class="pl-c"><span class="pl-c">#</span> Make an Excel package, example.com-example_data_package-2017-us-1.xlsx</span>
$ metapack -z <span class="pl-c"><span class="pl-c">#</span> Make a ZIP package, example.com-example_data_package-2017-us-1.zip</span></pre></div>
<p>The Excel package, <code>example-package.xlsx</code> will have the Metatab metadata from metata.csv in the <code>Meta</code> tab, and will have one tab per resource from the Resources section. The ZIP package <code>example-package.zip</code> will have all of the resources in the <code>data</code> directory and will also include the metadata in <a href="http://specs.frictionlessdata.io/tabular-data-package/">Tabular Data Package</a> format in the <code>datapackage.json</code> file. You can interate over the resources in these packages too:</p>
<div class="highlight highlight-source-shell"><pre>$ metapack -R example.com-example_data_package-2017-us-1.zip#simple-example
$ metapack -R example.com-example_data_package-2017-us-1.xlsx#simple-example</pre></div>
<p>The <code>metapack -R</code> also works with URLs:</p>
<div class="highlight highlight-source-shell"><pre>$ metapack -R http://devel.metatab.org/excel/example.com-example_data_package-2017-us-1.xlsx#simple-example
$ metapack -R http://devel.metatab.org/excel/example.com-example_data_package-2017-us-1.zip#simple-example</pre></div>
<p>And, you can access the packages in Python:</p>
<div class="highlight highlight-source-python"><pre><span class="pl-k">import</span> metatab

doc <span class="pl-k">=</span> metatab.open_package(<span class="pl-s"><span class="pl-pds">'</span>example-package.zip<span class="pl-pds">'</span></span>)
<span class="pl-c"><span class="pl-c">#</span> Or</span>
doc <span class="pl-k">=</span> metatab.open_package(<span class="pl-s"><span class="pl-pds">'</span>example-package.xlsx<span class="pl-pds">'</span></span>)</pre></div>
<p>Note that the data files in a derived package may be different that the ones in the source directory package. The derived data files will always have a header on the first line and data starting on the second line. The header will be taken from the data file's schema, using the <code>Table.Column</code> term value as the header name, or the <code>AltName</code> property, if it is defined. The names are always "slugified" to remove characters other than '-', '_' and '.' and will always be lowercase, with initial numbers removed.</p>
<p>If the <code>Datafile</code> term has a <code>StartLine</code> property, the values will be used in generating the data in derived packages to select the first line for yielding data rows. ( The <code>HeaderLines</code> property is used to build the schema, from which the header line is generated. )</p>
<a name="user-content-publishing-packages"></a>
<h2><a id="user-content-publishing-packages" class="anchor" href="#publishing-packages" aria-hidden="true"><svg aria-hidden="true" class="octicon octicon-link" height="16" version="1.1" viewBox="0 0 16 16" width="16"><path fill-rule="evenodd" d="M4 9h1v1H4c-1.5 0-3-1.69-3-3.5S2.55 3 4 3h4c1.45 0 3 1.69 3 3.5 0 1.41-.91 2.72-2 3.25V8.59c.58-.45 1-1.27 1-2.09C10 5.22 8.98 4 8 4H4c-.98 0-2 1.22-2 2.5S3 9 4 9zm9-3h-1v1h1c1 0 2 1.22 2 2.5S13.98 12 13 12H9c-.98 0-2-1.22-2-2.5 0-.83.42-1.64 1-2.09V6.25c-1.09.53-2 1.84-2 3.25C6 11.31 7.55 13 9 13h4c1.45 0 3-1.69 3-3.5S14.5 6 13 6z"></path></svg></a>Publishing Packages</h2>
<p>The <code>metasync</code> program can build multiple package types and upload them to an S3 bucket. Typical usage is:</p>
<div class="highlight highlight-source-shell"><pre>$ metasync -c -e -f -z -s s3://library.metatab.org</pre></div>
<p>With these options, the <code>metasync</code> program will create an Excel, Zip and Filesystem package and store them in the s3 bucket <code>library.metadata.org</code>. In this case, the "filesystem" package is not created in the local filesystem, but only in S3. ( "Filesystem" packages are basically what you get after unziping a ZIP package. )</p>
<p>Because generating all of the packages and uploading to S3 is common, the metasync -S option is a synonym for generating all package types and uploading:</p>
<div class="highlight highlight-source-shell"><pre>$ metasync -S s3://library.metatab.org</pre></div>
<p>Currently, <code>metasync</code> will only write packages to S3. For S3 <code>metasync</code> uses boto3, so refer to the <a href="http://boto3.readthedocs.io/en/latest/guide/configuration.html">boto3 credentials documentation</a> for instructions on how to set your S3 access key and secret.</p>
<p>One important side effect of the <code>metasync</code> program is that it will add <code>Distribution</code> terms to the main <code>metadata.csv</code> file before creating the packages, so all the packages that the program syncs will include references to the S3 location of all packages. For instance, the example invocation above will add these <code>Distribution</code> terms:</p>
<pre>Distribution        http://s3.amazonaws.com/library.metatab.org/simple_example-2017-us-1.xlsx
Distribution        http://s3.amazonaws.com/library.metatab.org/simple_example-2017-us-1.zip
Distribution        http://s3.amazonaws.com/library.metatab.org/simple_example-2017-us-1/metadata.csv
</pre>
<p>These <code>Distribution</code> terms are valuable documentation, but they are also required for the <code>metakan</code> program to create entries for the package in CKAN.</p>
<a name="user-content-adding-packages-to-ckan"></a>
<h3><a id="user-content-adding-packages-to-ckan" class="anchor" href="#adding-packages-to-ckan" aria-hidden="true"><svg aria-hidden="true" class="octicon octicon-link" height="16" version="1.1" viewBox="0 0 16 16" width="16"><path fill-rule="evenodd" d="M4 9h1v1H4c-1.5 0-3-1.69-3-3.5S2.55 3 4 3h4c1.45 0 3 1.69 3 3.5 0 1.41-.91 2.72-2 3.25V8.59c.58-.45 1-1.27 1-2.09C10 5.22 8.98 4 8 4H4c-.98 0-2 1.22-2 2.5S3 9 4 9zm9-3h-1v1h1c1 0 2 1.22 2 2.5S13.98 12 13 12H9c-.98 0-2-1.22-2-2.5 0-.83.42-1.64 1-2.09V6.25c-1.09.53-2 1.84-2 3.25C6 11.31 7.55 13 9 13h4c1.45 0 3-1.69 3-3.5S14.5 6 13 6z"></path></svg></a>Adding Packages to CKAN</h3>
<p>The <code>metakan</code> program reads a Metatab file, creates a dataset in CKAN, and adds resources to the CKAN entry based on the <code>Distribution</code> terms in the Metatab data. For instance, with a localhost CKAN server, and the metadata file from the "Publishing Packages" section example:</p>
<div class="highlight highlight-source-shell"><pre>$ metakan  --ckan http://localhost:32768/ --api f1f45...e9a9</pre></div>
<p>This command would create a CKAN dataset with the metadata in the <code>metadata.csv</code> file in the current directory, reading the <code>Distribution</code> terms. It would add resources for <code>simple_example-2017-us-1.xlsx</code> and <code>simple_example-2017-us-1.zip.</code> For the <code>simple_example-2017-us-1/metadata.csv</code> entry, it would read the remote <code>metadata.csv</code> file, resolve the resource URLs, and create a resource entry in CKAN for the <code>metadata.csv</code> file and all of the resources referenced in the remote <code>metadata.csv</code> file.</p>
<p>Note that because part of the information in the CKAN dataset comes from the loal <code>metadata.csv</code> file and part of the resources are discovered from the remote file, there is a substantial possibility for these files to become unsynchronized. For this reason, it is important to run the <code>metasync</code> program to create <code>Distribution</code> terms before running the <code>metakan</code> program.</p>
<p>For an example of a CKAN entry generated by <code>metakan</code>, see <a href="http://data.sandiegodata.org/dataset/fns-usda-gov-f2s_census-2015-2">http://data.sandiegodata.org/dataset/fns-usda-gov-f2s_census-2015-2</a></p>
<a name="user-content-publish-to-ckan-from-s3"></a>
<h4><a id="user-content-publish-to-ckan-from-s3" class="anchor" href="#publish-to-ckan-from-s3" aria-hidden="true"><svg aria-hidden="true" class="octicon octicon-link" height="16" version="1.1" viewBox="0 0 16 16" width="16"><path fill-rule="evenodd" d="M4 9h1v1H4c-1.5 0-3-1.69-3-3.5S2.55 3 4 3h4c1.45 0 3 1.69 3 3.5 0 1.41-.91 2.72-2 3.25V8.59c.58-.45 1-1.27 1-2.09C10 5.22 8.98 4 8 4H4c-.98 0-2 1.22-2 2.5S3 9 4 9zm9-3h-1v1h1c1 0 2 1.22 2 2.5S13.98 12 13 12H9c-.98 0-2-1.22-2-2.5 0-.83.42-1.64 1-2.09V6.25c-1.09.53-2 1.84-2 3.25C6 11.31 7.55 13 9 13h4c1.45 0 3-1.69 3-3.5S14.5 6 13 6z"></path></svg></a>Publish to CKAN from S3</h4>
<p>The <code>metakan</code> program can publish all of the CSV packages available in an S3 bucket by giving it an S3 url instead of a Metatab file. For instance, to publish all of the CSV packages in the <a href="#id2">``</a>library.metatab.org `` bucket, run:</p>
<div class="highlight highlight-source-shell"><pre>$ metakan  --ckan http://localhost:32768/ --api f1f45...e9a9 s3://library.metatab.org</pre></div>
<p>As with publishing a local Metatab file, the CSV packages in the S3 buck may have <code>Distribution</code> terms to identify other packages that should also be published into the CKan dataset.</p>
<a name="user-content-adding-packages-to-data-world"></a>
<h3><a id="user-content-adding-packages-to-dataworld" class="anchor" href="#adding-packages-to-dataworld" aria-hidden="true"><svg aria-hidden="true" class="octicon octicon-link" height="16" version="1.1" viewBox="0 0 16 16" width="16"><path fill-rule="evenodd" d="M4 9h1v1H4c-1.5 0-3-1.69-3-3.5S2.55 3 4 3h4c1.45 0 3 1.69 3 3.5 0 1.41-.91 2.72-2 3.25V8.59c.58-.45 1-1.27 1-2.09C10 5.22 8.98 4 8 4H4c-.98 0-2 1.22-2 2.5S3 9 4 9zm9-3h-1v1h1c1 0 2 1.22 2 2.5S13.98 12 13 12H9c-.98 0-2-1.22-2-2.5 0-.83.42-1.64 1-2.09V6.25c-1.09.53-2 1.84-2 3.25C6 11.31 7.55 13 9 13h4c1.45 0 3-1.69 3-3.5S14.5 6 13 6z"></path></svg></a>Adding Packages to Data.World</h3>
<p>The <code>metaworld</code> program will publish the package to <a href="http://data.world">Data.World</a>.  Only Excel and CSV packages will be published, because ZIP packages will be disaggregated, conflicting with CSV packages. The program is a bit buggy, and when creating a new package, the server may return a 500 error. If it does, just re-run the program.</p>
<p>The <code>metaworld</code> program takes no options. To use it, you must install the <a href="https://github.com/datadotworld/data.world-py">datadotworld python package</a> and configure it, which will store your username and password.</p>
<div class="highlight highlight-source-shell"><pre>$ metaworld</pre></div>
<a name="user-content-publishing-with-docker"></a>
<h3><a id="user-content-publishing-with-docker" class="anchor" href="#publishing-with-docker" aria-hidden="true"><svg aria-hidden="true" class="octicon octicon-link" height="16" version="1.1" viewBox="0 0 16 16" width="16"><path fill-rule="evenodd" d="M4 9h1v1H4c-1.5 0-3-1.69-3-3.5S2.55 3 4 3h4c1.45 0 3 1.69 3 3.5 0 1.41-.91 2.72-2 3.25V8.59c.58-.45 1-1.27 1-2.09C10 5.22 8.98 4 8 4H4c-.98 0-2 1.22-2 2.5S3 9 4 9zm9-3h-1v1h1c1 0 2 1.22 2 2.5S13.98 12 13 12H9c-.98 0-2-1.22-2-2.5 0-.83.42-1.64 1-2.09V6.25c-1.09.53-2 1.84-2 3.25C6 11.31 7.55 13 9 13h4c1.45 0 3-1.69 3-3.5S14.5 6 13 6z"></path></svg></a>Publishing With Docker</h3>
<p>The time require to run <code>metasync</code> to build and publish packages is often limited by network bandwidth, and can be much faster if run from a hosting service with a high bandwith connection, like AWS EC2. The <code>metasync</code> supports remote operation with the <code>--docker</code> option, which will re-run the program in docker.</p>
<p>To build the docker container, run <code>make build</code> in the <code>docker</code> directory in this github repository. Then add the <code>-D</code> or <code>--docker</code> option to the <code>metasync</code> command. The metatab document must be explicit, and must be acessible from the network.</p>
<div class="highlight highlight-source-shell"><pre>$ metasync -D -S s3://library.metatab.org http://devel.metatab.org/example.com-simple_example-2017-us-1.csv</pre></div>

</article>
  </div>

</div>

<button type="button" data-facebox="#jump-to-line" data-facebox-class="linejump" data-hotkey="l" class="d-none">Jump to Line</button>
<div id="jump-to-line" style="display:none">
  <!-- '"` --><!-- </textarea></xmp> --></option></form><form accept-charset="UTF-8" action="" class="js-jump-to-line-form" method="get"><div style="margin:0;padding:0;display:inline"><input name="utf8" type="hidden" value="&#x2713;" /></div>
    <input class="form-control linejump-input js-jump-to-line-field" type="text" placeholder="Jump to line&hellip;" aria-label="Jump to line" autofocus>
    <button type="submit" class="btn">Go</button>
</form></div>


  </div>
  <div class="modal-backdrop js-touch-events"></div>
</div>

    </div>
  </div>

  </div>

      <div class="container site-footer-container">
  <div class="site-footer" role="contentinfo">
    <ul class="site-footer-links float-right">
        <li><a href="https://github.com/contact" data-ga-click="Footer, go to contact, text:contact">Contact GitHub</a></li>
      <li><a href="https://developer.github.com" data-ga-click="Footer, go to api, text:api">API</a></li>
      <li><a href="https://training.github.com" data-ga-click="Footer, go to training, text:training">Training</a></li>
      <li><a href="https://shop.github.com" data-ga-click="Footer, go to shop, text:shop">Shop</a></li>
        <li><a href="https://github.com/blog" data-ga-click="Footer, go to blog, text:blog">Blog</a></li>
        <li><a href="https://github.com/about" data-ga-click="Footer, go to about, text:about">About</a></li>

    </ul>

    <a href="https://github.com" aria-label="Homepage" class="site-footer-mark" title="GitHub">
      <svg aria-hidden="true" class="octicon octicon-mark-github" height="24" version="1.1" viewBox="0 0 16 16" width="24"><path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>
</a>
    <ul class="site-footer-links">
      <li>&copy; 2017 <span title="0.36983s from github-fe152-cp1-prd.iad.github.net">GitHub</span>, Inc.</li>
        <li><a href="https://github.com/site/terms" data-ga-click="Footer, go to terms, text:terms">Terms</a></li>
        <li><a href="https://github.com/site/privacy" data-ga-click="Footer, go to privacy, text:privacy">Privacy</a></li>
        <li><a href="https://github.com/security" data-ga-click="Footer, go to security, text:security">Security</a></li>
        <li><a href="https://status.github.com/" data-ga-click="Footer, go to status, text:status">Status</a></li>
        <li><a href="https://help.github.com" data-ga-click="Footer, go to help, text:help">Help</a></li>
    </ul>
  </div>
</div>



  

  <div id="ajax-error-message" class="ajax-error-message flash flash-error">
    <svg aria-hidden="true" class="octicon octicon-alert" height="16" version="1.1" viewBox="0 0 16 16" width="16"><path fill-rule="evenodd" d="M8.865 1.52c-.18-.31-.51-.5-.87-.5s-.69.19-.87.5L.275 13.5c-.18.31-.18.69 0 1 .19.31.52.5.87.5h13.7c.36 0 .69-.19.86-.5.17-.31.18-.69.01-1L8.865 1.52zM8.995 13h-2v-2h2v2zm0-3h-2V6h2v4z"/></svg>
    <button type="button" class="flash-close js-flash-close js-ajax-error-dismiss" aria-label="Dismiss error">
      <svg aria-hidden="true" class="octicon octicon-x" height="16" version="1.1" viewBox="0 0 12 16" width="12"><path fill-rule="evenodd" d="M7.48 8l3.75 3.75-1.48 1.48L6 9.48l-3.75 3.75-1.48-1.48L4.52 8 .77 4.25l1.48-1.48L6 6.52l3.75-3.75 1.48 1.48z"/></svg>
    </button>
    You can't perform that action at this time.
  </div>


    <script crossorigin="anonymous" src="https://assets-cdn.github.com/assets/compat-8a4318ffea09a0cdb8214b76cf2926b9f6a0ced318a317bed419db19214c690d.js"></script>
    <script crossorigin="anonymous" src="https://assets-cdn.github.com/assets/frameworks-6d109e75ad8471ba415082726c00c35fb929ceab975082492835f11eca8c07d9.js"></script>
    <script async="async" crossorigin="anonymous" src="https://assets-cdn.github.com/assets/github-7a2dddb6ff90d0ce87a6c47aa030f228d886655501e9badc4856739bbed90371.js"></script>
    
    
    
    
  <div class="js-stale-session-flash stale-session-flash flash flash-warn flash-banner d-none">
    <svg aria-hidden="true" class="octicon octicon-alert" height="16" version="1.1" viewBox="0 0 16 16" width="16"><path fill-rule="evenodd" d="M8.865 1.52c-.18-.31-.51-.5-.87-.5s-.69.19-.87.5L.275 13.5c-.18.31-.18.69 0 1 .19.31.52.5.87.5h13.7c.36 0 .69-.19.86-.5.17-.31.18-.69.01-1L8.865 1.52zM8.995 13h-2v-2h2v2zm0-3h-2V6h2v4z"/></svg>
    <span class="signed-in-tab-flash">You signed in with another tab or window. <a href="">Reload</a> to refresh your session.</span>
    <span class="signed-out-tab-flash">You signed out in another tab or window. <a href="">Reload</a> to refresh your session.</span>
  </div>
  <div class="facebox" id="facebox" style="display:none;">
  <div class="facebox-popup">
    <div class="facebox-content" role="dialog" aria-labelledby="facebox-header" aria-describedby="facebox-description">
    </div>
    <button type="button" class="facebox-close js-facebox-close" aria-label="Close modal">
      <svg aria-hidden="true" class="octicon octicon-x" height="16" version="1.1" viewBox="0 0 12 16" width="12"><path fill-rule="evenodd" d="M7.48 8l3.75 3.75-1.48 1.48L6 9.48l-3.75 3.75-1.48-1.48L4.52 8 .77 4.25l1.48-1.48L6 6.52l3.75-3.75 1.48 1.48z"/></svg>
    </button>
  </div>
</div>


  </body>
</html>

