import Foundation
import Observation

enum Format: String, CaseIterable, Identifiable {
    case reel = "Reel 9:16"
    case youtube = "YouTube 16:9"
    case both = "Both"
    var id: String { rawValue }
}

enum Look: String, CaseIterable, Identifiable {
    case auto = "Lyrics (auto)"
    case visualizer = "Visualizer"
    var id: String { rawValue }
}

@Observable
final class Job: Identifiable {
    enum Status: Equatable { case queued, rendering, done, failed(String) }

    let id = UUID()
    let source: URL?
    let vertical: Bool
    let output: URL
    var status: Status
    var progress: Double = 0
    var stage = ""
    var mode = ""

    init(source: URL?, vertical: Bool, output: URL, status: Status = .queued) {
        self.source = source
        self.vertical = vertical
        self.output = output
        self.status = status
    }

    var title: String {
        (source ?? output).deletingPathExtension().lastPathComponent
    }
}

@MainActor
@Observable
final class Engine {
    var jobs: [Job] = []
    var selection: Job.ID?
    var format: Format = .reel
    var look: Look = .auto
    var palette = "dusk"
    var align = "center"
    var isRunning = false

    let repo = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("lyrics-video-tool")
    var outputDir: URL { repo.appendingPathComponent("output") }

    static let audioExtensions: Set<String> = ["mp3", "m4a", "wav", "flac", "aac", "aif", "aiff", "ogg", "opus"]

    init() { loadExisting() }

    var selectedJob: Job? { jobs.first { $0.id == selection } }

    /// Previously rendered videos show up as finished jobs so the app doubles as the gallery.
    func loadExisting() {
        try? FileManager.default.createDirectory(at: outputDir, withIntermediateDirectories: true)
        let files = (try? FileManager.default.contentsOfDirectory(
            at: outputDir, includingPropertiesForKeys: [.contentModificationDateKey])) ?? []
        let videos = files.filter { $0.pathExtension == "mp4" }.sorted {
            let a = (try? $0.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate) ?? .distantPast
            let b = (try? $1.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate) ?? .distantPast
            return a > b
        }
        jobs = videos.map { url in
            let name = url.lastPathComponent
            let job = Job(source: nil, vertical: name.contains("_reel") || name.contains("_vert"),
                          output: url, status: .done)
            job.progress = 1
            return job
        }
        selection = jobs.first?.id
    }

    func add(_ urls: [URL]) {
        let audio = urls.filter { Self.audioExtensions.contains($0.pathExtension.lowercased()) }
        var added: [Job] = []
        for url in audio {
            let orientations: [Bool] = switch format {
            case .reel: [true]
            case .youtube: [false]
            case .both: [true, false]
            }
            for vertical in orientations {
                let name = safeName(url.deletingPathExtension().lastPathComponent) + (vertical ? "_reel" : "_youtube")
                added.append(Job(source: url, vertical: vertical, output: outputDir.appendingPathComponent(name + ".mp4")))
            }
        }
        jobs.insert(contentsOf: added, at: 0)
        if selection == nil { selection = added.first?.id }
        start()
    }

    func remove(_ job: Job) {
        jobs.removeAll { $0.id == job.id }
    }

    func start() {
        guard !isRunning else { return }
        isRunning = true
        Task {
            while let job = jobs.last(where: { $0.status == .queued }) {
                await run(job)
            }
            isRunning = false
        }
    }

    private func safeName(_ s: String) -> String {
        let allowed = CharacterSet.alphanumerics.union(CharacterSet(charactersIn: "-_ "))
        let cleaned = String(String.UnicodeScalarView(s.unicodeScalars.map { allowed.contains($0) ? $0 : " " }))
        return cleaned.split(separator: " ").joined(separator: "_").prefix(80).description
    }

    private func python() -> String {
        for p in ["/opt/homebrew/bin/python3", "/usr/local/bin/python3", "/usr/bin/python3"]
        where FileManager.default.isExecutableFile(atPath: p) { return p }
        return "/usr/bin/python3"
    }

    private func run(_ job: Job) async {
        guard let source = job.source else { return }
        job.status = .rendering
        job.stage = "starting"
        var args = [repo.appendingPathComponent("create_video.py").path,
                    "--audio", source.path,
                    "--output", job.output.path,
                    "--palette", palette,
                    "--align", job.vertical ? align : "left"]
        if job.vertical { args.append("--vertical") }
        if look == .visualizer { args.append("--visualizer") }

        let process = Process()
        process.executableURL = URL(fileURLWithPath: python())
        process.arguments = args
        process.currentDirectoryURL = repo
        var env = ProcessInfo.processInfo.environment
        env["PATH"] = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:" + (env["PATH"] ?? "")
        env["PYTHONUNBUFFERED"] = "1"
        process.environment = env
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe

        let tail = TailBuffer()
        pipe.fileHandleForReading.readabilityHandler = { handle in
            let data = handle.availableData
            guard !data.isEmpty, let text = String(data: data, encoding: .utf8) else { return }
            tail.append(text)
            for line in text.split(separator: "\n") {
                let parts = line.split(separator: " ", maxSplits: 2)
                if parts.first == "PROGRESS", parts.count >= 2, let p = Double(parts[1]) {
                    let stage = parts.count > 2 ? String(parts[2]) : ""
                    Task { @MainActor in job.progress = p; job.stage = stage }
                } else if parts.first == "MODE", parts.count >= 2 {
                    let mode = String(parts[1])
                    Task { @MainActor in job.mode = mode }
                }
            }
        }

        let status: Int32 = await withCheckedContinuation { cont in
            process.terminationHandler = { cont.resume(returning: $0.terminationStatus) }
            do { try process.run() } catch {
                cont.resume(returning: -1)
            }
        }
        pipe.fileHandleForReading.readabilityHandler = nil

        if status == 0, FileManager.default.fileExists(atPath: job.output.path) {
            job.status = .done
            job.progress = 1
            if selection == nil || selectedJob?.status != .done { selection = job.id }
        } else {
            job.status = .failed(tail.lastLines(6))
        }
    }
}

/// Thread-safe rolling log so a failed render can show why.
final class TailBuffer: @unchecked Sendable {
    private var text = ""
    private let lock = NSLock()
    func append(_ s: String) {
        lock.lock(); text = String((text + s).suffix(4000)); lock.unlock()
    }
    func lastLines(_ n: Int) -> String {
        lock.lock(); defer { lock.unlock() }
        return text.split(separator: "\n").filter { !$0.hasPrefix("PROGRESS") }.suffix(n).joined(separator: "\n")
    }
}
