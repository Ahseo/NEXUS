"use client";

import { useState } from "react";

interface AddPersonModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (person: PersonData) => Promise<void>;
}

export interface PersonData {
  name: string;
  title: string;
  company: string;
  role: string;
  linkedin: string;
  twitter: string;
  github: string;
  avatar_url: string;
  topics: string[];
}

export function AddPersonModal({ isOpen, onClose, onAdd }: AddPersonModalProps) {
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState<PersonData>({
    name: "",
    title: "",
    company: "",
    role: "participant",
    linkedin: "",
    twitter: "",
    github: "",
    avatar_url: "",
    topics: [],
  });
  const [topicInput, setTopicInput] = useState("");

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    
    setLoading(true);
    try {
      await onAdd(form);
      setForm({
        name: "",
        title: "",
        company: "",
        role: "participant",
        linkedin: "",
        twitter: "",
        github: "",
        avatar_url: "",
        topics: [],
      });
      onClose();
    } finally {
      setLoading(false);
    }
  };

  const addTopic = () => {
    if (topicInput.trim() && !form.topics.includes(topicInput.trim())) {
      setForm({ ...form, topics: [...form.topics, topicInput.trim()] });
      setTopicInput("");
    }
  };

  const removeTopic = (topic: string) => {
    setForm({ ...form, topics: form.topics.filter(t => t !== topic) });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div 
        className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl"
        onClick={e => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900">Add Person</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">&times;</button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
            <input
              type="text"
              value={form.name}
              onChange={e => setForm({ ...form, name: e.target.value })}
              className="w-full rounded-lg border border-gray-200 px-3 py-2 text-gray-900 placeholder-gray-400 focus:border-indigo-500 focus:outline-none"
              placeholder="John Doe"
              required
            />
          </div>

          {/* Title & Company */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
              <input
                type="text"
                value={form.title}
                onChange={e => setForm({ ...form, title: e.target.value })}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-gray-900 placeholder-gray-400 focus:border-indigo-500 focus:outline-none"
                placeholder="Software Engineer"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Company</label>
              <input
                type="text"
                value={form.company}
                onChange={e => setForm({ ...form, company: e.target.value })}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-gray-900 placeholder-gray-400 focus:border-indigo-500 focus:outline-none"
                placeholder="Acme Inc"
              />
            </div>
          </div>

          {/* Role */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
            <select
              value={form.role}
              onChange={e => setForm({ ...form, role: e.target.value })}
              className="w-full rounded-lg border border-gray-200 px-3 py-2 text-gray-900 focus:border-indigo-500 focus:outline-none"
            >
              <option value="participant">Participant</option>
              <option value="speaker">Speaker</option>
              <option value="judge">Judge</option>
              <option value="organizer">Organizer</option>
              <option value="sponsor">Sponsor</option>
            </select>
          </div>

          {/* SNS Links */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">Social Links</label>
            <input
              type="url"
              value={form.linkedin}
              onChange={e => setForm({ ...form, linkedin: e.target.value })}
              className="w-full rounded-lg border border-gray-200 px-3 py-2 text-gray-900 placeholder-gray-400 focus:border-indigo-500 focus:outline-none"
              placeholder="LinkedIn URL"
            />
            <div className="grid grid-cols-2 gap-2">
              <input
                type="text"
                value={form.twitter}
                onChange={e => setForm({ ...form, twitter: e.target.value })}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-gray-900 placeholder-gray-400 focus:border-indigo-500 focus:outline-none"
                placeholder="Twitter handle"
              />
              <input
                type="text"
                value={form.github}
                onChange={e => setForm({ ...form, github: e.target.value })}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-gray-900 placeholder-gray-400 focus:border-indigo-500 focus:outline-none"
                placeholder="GitHub username"
              />
            </div>
          </div>

          {/* Topics */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Topics</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={topicInput}
                onChange={e => setTopicInput(e.target.value)}
                onKeyDown={e => e.key === "Enter" && (e.preventDefault(), addTopic())}
                className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-gray-900 placeholder-gray-400 focus:border-indigo-500 focus:outline-none"
                placeholder="AI, ML, etc."
              />
              <button
                type="button"
                onClick={addTopic}
                className="rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200"
              >
                Add
              </button>
            </div>
            {form.topics.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {form.topics.map(topic => (
                  <span
                    key={topic}
                    className="inline-flex items-center gap-1 rounded-full bg-indigo-50 px-2 py-0.5 text-xs text-indigo-600"
                  >
                    {topic}
                    <button type="button" onClick={() => removeTopic(topic)} className="hover:text-indigo-800">&times;</button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Submit */}
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !form.name.trim()}
              className="rounded-lg bg-[#1a1a1a] px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
            >
              {loading ? "Adding..." : "Add Person"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
