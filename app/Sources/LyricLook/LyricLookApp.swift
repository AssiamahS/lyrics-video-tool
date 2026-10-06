import SwiftUI
import AVKit
import UniformTypeIdentifiers

@main
struct LyricLookApp: App {
    @State private var engine = Engine()

    var body: some Scene {
        WindowGroup("LyricLook") {
            ContentView()
                .environment(engine)
                .frame(minWidth: 1040, minHeight: 680)
        }
        .commands {
            CommandGroup(replacing: .newItem) {
                Button("Add Songs…") { AddSongs.present(engine) }
                    .keyboardShortcut("o")
            }
        }
    }
}

enum AddSongs {
    @MainActor
    static func present(_ engine: Engine) {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = true
        panel.canChooseDirectories = false
        panel.allowedContentTypes = [.audio]
        panel.directoryURL = FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Music/yt-dlp")
        panel.prompt = "Make Videos"
        if panel.runModal() == .OK { engine.add(panel.urls) }
    }
}

struct ContentView: View {
    @Environment(Engine.self) private var engine
    @State private var dropTargeted = false

    var body: some View {
        @Bindable var engine = engine
        NavigationSplitView {
            List(selection: $engine.selection) {
                ForEach(engine.jobs) { job in
                    JobRow(job: job)
                        .tag(job.id)
                        .contextMenu {
                            Button("Show in Finder") { NSWorkspace.shared.activateFileViewerSelecting([job.output]) }
                                .disabled(job.status != .done)
                            Button("Remove from List") { engine.remove(job) }
                        }
                }
            }
            .navigationSplitViewColumnWidth(min: 280, ideal: 320)
            .overlay {
                if engine.jobs.isEmpty {
                    ContentUnavailableView("No videos yet", systemImage: "music.note.list",
                                           description: Text("Drop songs here or press ⌘O"))
                }
            }
        } detail: {
            Detail(job: engine.selectedJob)
        }
        .toolbar {
            ToolbarItemGroup(placement: .principal) {
                Picker("Format", selection: $engine.format) {
                    ForEach(Format.allCases) { Text($0.rawValue).tag($0) }
                }
                .pickerStyle(.segmented)
                .frame(width: 280)
                Picker("Look", selection: $engine.look) {
                    ForEach(Look.allCases) { Text($0.rawValue).tag($0) }
                }
                .frame(width: 140)
                .labelsHidden()
                Picker("Palette", selection: $engine.palette) {
                    ForEach(["dusk", "ocean", "ember", "mono"], id: \.self) { Text($0.capitalized).tag($0) }
                }
                .frame(width: 90)
                .labelsHidden()
            }
            ToolbarItem(placement: .primaryAction) {
                Button { AddSongs.present(engine) } label: {
                    Label("Add Songs", systemImage: "plus")
                }
            }
            ToolbarItem(placement: .primaryAction) {
                Button { NSWorkspace.shared.open(engine.outputDir) } label: {
                    Label("Output Folder", systemImage: "folder")
                }
            }
        }
        .dropDestination(for: URL.self) { urls, _ in
            engine.add(urls)
            return true
        } isTargeted: { dropTargeted = $0 }
        .overlay {
            if dropTargeted {
                RoundedRectangle(cornerRadius: 16)
                    .strokeBorder(.tint, style: StrokeStyle(lineWidth: 3, dash: [10]))
                    .padding(8)
                    .allowsHitTesting(false)
            }
        }
    }
}

struct JobRow: View {
    let job: Job

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: job.vertical ? "rectangle.portrait" : "rectangle")
                .foregroundStyle(.secondary)
                .frame(width: 18)
            VStack(alignment: .leading, spacing: 4) {
                Text(job.title).lineLimit(1)
                switch job.status {
                case .queued:
                    Text("Queued").font(.caption).foregroundStyle(.secondary)
                case .rendering:
                    ProgressView(value: job.progress)
                    Text("\(job.stage) \(Int(job.progress * 100))%\(job.mode.isEmpty ? "" : " · \(job.mode)")")
                        .font(.caption).foregroundStyle(.secondary)
                case .done:
                    Text(job.mode.isEmpty ? (job.vertical ? "Reel" : "YouTube") : "\(job.vertical ? "Reel" : "YouTube") · \(job.mode)")
                        .font(.caption).foregroundStyle(.secondary)
                case .failed:
                    Text("Failed").font(.caption).foregroundStyle(.red)
                }
            }
        }
        .padding(.vertical, 3)
    }
}

struct Detail: View {
    let job: Job?
    @State private var player = AVPlayer()

    var body: some View {
        Group {
            if let job {
                switch job.status {
                case .done:
                    VStack(spacing: 12) {
                        VideoPlayer(player: player)
                            .aspectRatio(job.vertical ? 9.0 / 16.0 : 16.0 / 9.0, contentMode: .fit)
                            .clipShape(RoundedRectangle(cornerRadius: 12))
                            .shadow(radius: 20)
                        HStack {
                            Text(job.output.lastPathComponent).font(.callout).foregroundStyle(.secondary)
                            Spacer()
                            Button("Show in Finder") { NSWorkspace.shared.activateFileViewerSelecting([job.output]) }
                            Button("Open in QuickTime") { NSWorkspace.shared.open(job.output) }
                        }
                    }
                    .padding(24)
                case .rendering, .queued:
                    VStack(spacing: 14) {
                        ProgressView(value: job.progress).frame(width: 320)
                        Text(job.status == .queued ? "Waiting in queue…" : "Rendering \(job.title) — \(Int(job.progress * 100))%")
                            .foregroundStyle(.secondary)
                    }
                case .failed(let log):
                    VStack(alignment: .leading, spacing: 10) {
                        Label("Render failed", systemImage: "exclamationmark.triangle").font(.title3)
                        ScrollView {
                            Text(log).font(.system(.caption, design: .monospaced)).textSelection(.enabled)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }
                    .padding(24)
                }
            } else {
                ContentUnavailableView("Pick a video", systemImage: "play.rectangle",
                                       description: Text("Finished renders play here"))
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(.black.opacity(0.92))
        .onChange(of: job?.id, initial: true) { load() }
        .onChange(of: job?.status) { load() }
    }

    private func load() {
        guard let job, job.status == .done else { player.pause(); return }
        player.replaceCurrentItem(with: AVPlayerItem(url: job.output))
        player.play()
    }
}
