#!/usr/bin/ruby
# Downloaded from https://gist.github.com/Milly/909564

require 'rubygems'
require 'rubygems/commands/fetch_command'

class Gem::Commands::FetchCommand
  def add_version_option_with_fetch_depends
    add_version_option_without_fetch_depends
    add_option('-y', '--[no-]dependencies',
               "Fetch dependent gems") do |value, options|
      options[:dependencies] = value
    end
  end

  def get_all_gem_names_with_fetch_depends
    @dependent_gem_names || get_all_gem_names_without_fetch_depends
  end

  def execute_with_fetch_depends
    execute_without_fetch_depends
    if options[:dependencies] then
      @dependent_gem_names = get_dependent_gem_names
      options[:version] = nil
      execute_without_fetch_depends
    end
  end

  [:add_version_option, :get_all_gem_names, :execute].each do |target|
    feature = "fetch_depends"
    alias_method "#{target}_without_#{feature}", target
    alias_method target, "#{target}_with_#{feature}"
  end

private
  def get_dependent_gem_names
    version = options[:version] || Gem::Requirement.default
    request_gem_names = get_all_gem_names_without_fetch_depends.uniq
    to_do = fetch_specs_by_names_and_version(request_gem_names, version)
    seen = {}

    until to_do.empty? do
      spec = to_do.shift
      next if spec.nil? or seen[spec.name]
      seen[spec.name] = true
      deps = spec.runtime_dependencies
      deps.each do |dep|
        requirements = dep.requirement.requirements.map { |req,| req }
        all = !dep.prerelease? and
              (requirements.length > 1 or
                (requirements.first != ">=" and requirements.first != ">"))
        result = fetch_spec(dep, all)
        to_do.push(result)
      end
    end

    gem_names = seen.map { |name,| name }
    gem_names.reject { |name| request_gem_names.include? name }
  end

  def fetch_specs_by_names_and_version(gem_names, version)
    all = Gem::Requirement.default != version
    specs = gem_names.map do |gem_name|
      dep = Gem::Dependency.new(gem_name, version)
      dep.prerelease = options[:prerelease]
      fetch_spec(dep, all)
    end
    specs.compact
  end

  def fetch_spec(dep, all)
    specs_and_sources, errors =
      Gem::SpecFetcher.fetcher.fetch_with_errors(dep, all, true,
                                                 dep.prerelease?)
    if platform = Gem.platforms.last then
      filtered = specs_and_sources.select { |s,| s.platform == platform }
      specs_and_sources = filtered unless filtered.empty?
    end
    spec, source_uri = specs_and_sources.sort_by { |s,| s.version }.last
    spec
  end
end

load `which gem`.rstrip
