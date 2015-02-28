<?php

final class BabelLintEngine extends ArcanistLintEngine {

  public function buildLinters() {
    $flake8 = new ArcanistFlake8Linter();

    $pythonPaths = array();
    foreach ($this->getPaths() as $path) {
      if (!self::endsWith($path, ".py")) continue;  // Only include Python files.
      if (self::startsWith($path, "example/api/")) continue;  // Old crufty stuff.
      \array_push($pythonPaths, $path);
    }
    $flake8->setPaths($pythonPaths);

    return array(
      "flake8" => $flake8,
    );
  }

  public static function startsWith($haystack, $needle) {
    return \substr($haystack, 0, strlen($needle)) === $needle;
  }

  public static function endsWith($haystack, $needle) {
    return \substr($haystack, \strlen($haystack) - \strlen($needle)) === $needle;
  }
}
